#!/usr/bin/env python3
"""Install BuildingDepot: bare-metal services + containerized datastores.

Run from the repo root:

    python3 deploy/install.py                  # full install
    python3 deploy/install.py --no-service     # skip systemd units (CI/dev)
    python3 deploy/install.py --no-bootstrap   # skip admin user + ds1 registration
    python3 deploy/install.py --force-env      # re-provision .env from example
    python3 deploy/install.py --no-ask-sudo    # don't prompt before sudo (automation)
    python3 deploy/install.py --dev            # include mailpit SMTP catcher

Bare-metal: BD Python services (via uv + gunicorn), Valkey, RabbitMQ, nginx.
Docker (loopback only): MongoDB 7, InfluxDB 1.8, optionally mailpit.

The repo-root `.env` is the only config file: the BD services read it directly
through `buildingdepot/bd_config.py`, and compose reads it for the datastore
credentials. Nothing is rendered from it.

Idempotent: existing .env is left untouched (use --force-env to overwrite). TLS
is a separate root step handled by the host nginx — see the commands printed at
the end and docs/deployment.md.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY_DIR = os.path.join(REPO_ROOT, "deploy")
sys.path.insert(0, os.path.join(DEPLOY_DIR, "shared"))

import env as env_module  # noqa: E402
import log  # noqa: E402
import manifest  # noqa: E402
import packages  # noqa: E402
import proc  # noqa: E402
import systemd  # noqa: E402

ENV_EXAMPLE = os.path.join(REPO_ROOT, ".env.example")
ENV_DEST = os.path.join(REPO_ROOT, ".env")
COMPOSE_FILE = os.path.join(DEPLOY_DIR, "compose.yml")

RABBITMQ_CONF_SRC = os.path.join(DEPLOY_DIR, "rabbitmq", "rabbitmq.conf")
RABBITMQ_CONF_DEST = "/etc/rabbitmq/rabbitmq.conf"
RABBITMQ_PLUGINS_SRC = os.path.join(DEPLOY_DIR, "rabbitmq", "enabled_plugins")
RABBITMQ_PLUGINS_DEST = "/etc/rabbitmq/enabled_plugins"

SYSTEMD_DIR = os.path.join(DEPLOY_DIR, "systemd")
SERVICES = ("bd-replica", "bd-central", "bd-data")

# Infra secrets generated locally on first provision.
GENERATE_SECRETS = (
    "SECRET_KEY",
    "MONGODB_PWD",
    "INFLUXDB_PWD",
    "REDIS_PWD",
    "RABBITMQ_ADMIN_PWD",
    "RABBITMQ_ENDUSER_PWD",
    "BD_CLIENT_SECRET",
)

# BD .env key -> manifest key. Cross-app secrets from site.env; endpoint keys
# are not mapped because bare-metal BD always connects to localhost.
#
# These are credentials BD *registers* for other apps to use, not credentials BD
# consumes: the RabbitMQ end-user the UI subscribes with, and the OAuth client
# MitesBackend authenticates with. Declared in the manifest so they can exist
# before BD does; with no manifest, BD generates its own and stays standalone.
MANIFEST_MAP: dict[str, manifest.MappingValue] = {
    "RABBITMQ_ENDUSER_USERNAME": "RABBITMQ_END_USER",
    "RABBITMQ_ENDUSER_PWD": "RABBITMQ_END_PWD",
    "BD_CLIENT_ID": "BD_CLIENT_ID",
    "BD_CLIENT_SECRET": "BD_CLIENT_SECRET",
}

# Default site manifest location for a co-located host (sibling repo).
# Resolution honours $SITE_ENV first; absent any manifest, BD provisions
# from .env.example alone (standalone fallback).
DEFAULT_MANIFEST = os.path.join(os.path.dirname(REPO_ROOT), "Mites-Deploy", "site.env")

# Bare-metal apt packages.
APT_PACKAGES = ["valkey-server", "rabbitmq-server"]


# ---------------------------------------------------------------------------
# Steps (each idempotent)
# ---------------------------------------------------------------------------

def install_apt_packages() -> None:
    log.info("ensuring bare-metal packages")
    packages.apt_install(APT_PACKAGES)


def install_uv() -> str:
    log.info("ensuring uv")
    return packages.ensure_uv()


def uv_sync(uv_bin: str) -> None:
    log.info("syncing Python dependencies")
    proc.run([uv_bin, "sync", "--frozen"], cwd=REPO_ROOT)


def provision_env(force: bool) -> dict[str, str]:
    log.info("provisioning .env")
    manifest.apply_site_env(
        ENV_EXAMPLE,
        ENV_DEST,
        MANIFEST_MAP,
        generate=GENERATE_SECRETS,
        site_path=DEFAULT_MANIFEST,
        force=force,
    )
    return env_module.read_env(ENV_DEST)


def install_systemd_units(uv_bin: str) -> None:
    log.info("installing systemd user units")
    variables = {
        "WORKING_DIRECTORY": REPO_ROOT,
        "UV_BIN": uv_bin,
    }
    for name in SERVICES:
        unit = os.path.join(SYSTEMD_DIR, f"{name}.service.template")
        systemd.install_user_unit(unit, variables=variables)


def compose_up(dev: bool) -> None:
    packages.ensure_docker()
    log.info("bringing up datastore containers (loopback only)")
    argv = ["docker", "compose", "-f", COMPOSE_FILE, "--env-file", ENV_DEST]
    if dev:
        argv.extend(["--profile", "dev"])
    argv.extend(["up", "-d"])
    proc.run(argv, cwd=DEPLOY_DIR)


def configure_valkey(values: dict[str, str]) -> None:
    log.info("configuring Valkey")
    redis_pwd = values.get("REDIS_PWD", "")
    if not redis_pwd:
        log.die("REDIS_PWD is empty in .env — cannot configure Valkey")

    conf_dir = "/etc/valkey/valkey.conf.d"
    conf_path = os.path.join(conf_dir, "buildingdepot.conf")
    content = f"requirepass {redis_pwd}\nappendonly yes\nbind 127.0.0.1\n"

    if os.path.exists(conf_path):
        with open(conf_path, "r") as f:
            if f.read() == content:
                log.step("Valkey config already up to date")
                return

    tmp = "/tmp/valkey-buildingdepot.conf"
    with open(tmp, "w") as f:
        f.write(content)
    proc.sudo_run(["mkdir", "-p", conf_dir], reason="create Valkey conf.d")
    proc.sudo_run(
        ["cp", tmp, conf_path],
        reason="write Valkey password + persistence config",
        confirm=False,
    )
    os.unlink(tmp)
    _ensure_valkey_includes_conf_d()
    proc.sudo_run(["systemctl", "restart", "valkey-server"], reason="restart Valkey", confirm=False)
    log.ok("Valkey configured (password + appendonly + loopback)")


def _ensure_valkey_includes_conf_d() -> None:
    """Make sure /etc/valkey/valkey.conf includes the conf.d directory."""
    main_conf = "/etc/valkey/valkey.conf"
    include_line = "include /etc/valkey/valkey.conf.d/*.conf"
    if os.path.exists(main_conf):
        with open(main_conf, "r") as f:
            if include_line in f.read():
                return
    proc.sudo_run(
        ["sh", "-c", f"echo '{include_line}' >> {main_conf}"],
        reason="add conf.d include to Valkey config",
        confirm=False,
    )


def configure_rabbitmq(values: dict[str, str]) -> None:
    log.info("configuring RabbitMQ")

    proc.sudo_run(
        ["cp", RABBITMQ_CONF_SRC, RABBITMQ_CONF_DEST],
        reason="install RabbitMQ config",
    )

    proc.sudo_run(
        ["cp", RABBITMQ_PLUGINS_SRC, RABBITMQ_PLUGINS_DEST],
        reason="install RabbitMQ enabled plugins",
        confirm=False,
    )

    proc.sudo_run(["systemctl", "restart", "rabbitmq-server"], reason="restart RabbitMQ", confirm=False)

    # Wait for RabbitMQ to come up
    log.step("waiting for RabbitMQ to start")
    proc.sudo_run(
        ["rabbitmqctl", "await_startup"],
        reason="wait for RabbitMQ startup",
        confirm=False,
    )

    _rabbitmq_ensure_user(
        values.get("RABBITMQ_ADMIN_USERNAME", "bdadmin"),
        values.get("RABBITMQ_ADMIN_PWD", ""),
        tags="administrator",
        permissions=(".*", ".*", ".*"),
    )
    _rabbitmq_ensure_user(
        values.get("RABBITMQ_ENDUSER_USERNAME", "bduser"),
        values.get("RABBITMQ_ENDUSER_PWD", ""),
        tags="",
        permissions=("", "", ".*"),
    )
    log.ok("RabbitMQ configured (users + plugins + loopback)")


def _rabbitmq_ensure_user(
    username: str,
    password: str,
    *,
    tags: str,
    permissions: tuple[str, str, str],
) -> None:
    """Create or update a RabbitMQ user idempotently."""
    if not password:
        log.die(f"password for RabbitMQ user '{username}' is empty in .env")
    result = proc.sudo_run(
        ["rabbitmqctl", "list_users", "--formatter", "csv"],
        capture=True,
        confirm=False,
        reason=f"check if RabbitMQ user '{username}' exists",
    )
    if username in result.stdout:
        proc.sudo_run(
            ["rabbitmqctl", "change_password", username, password],
            confirm=False,
            reason=f"update password for RabbitMQ user '{username}'",
        )
    else:
        proc.sudo_run(
            ["rabbitmqctl", "add_user", username, password],
            confirm=False,
            reason=f"create RabbitMQ user '{username}'",
        )
    proc.sudo_run(
        ["rabbitmqctl", "set_user_tags", username, *(tags.split() if tags else [])],
        confirm=False,
        reason=f"set tags for '{username}'",
    )
    proc.sudo_run(
        ["rabbitmqctl", "set_permissions", "-p", "/", username, *permissions],
        confirm=False,
        reason=f"set permissions for '{username}'",
    )
    log.step(f"RabbitMQ user '{username}' ready")


def bootstrap(values: dict[str, str]) -> None:
    """Seed admin user, ds1 data service, and the OAuth client. Idempotent."""
    log.info("bootstrapping admin user, ds1 data service, and OAuth client")
    mongo_pwd = values.get("MONGODB_PWD", "")
    if not mongo_pwd:
        log.die("MONGODB_PWD is empty in .env — cannot bootstrap")

    argv = [
        "--mongo-user", values.get("MONGODB_USERNAME", "bdadmin"),
        "--mongo-pwd", mongo_pwd,
    ]
    client_id = values.get("BD_CLIENT_ID", "")
    client_secret = values.get("BD_CLIENT_SECRET", "")
    if client_id and client_secret:
        argv += ["--client-id", client_id, "--client-secret", client_secret]
    else:
        log.step("BD_CLIENT_ID/BD_CLIENT_SECRET unset — skipping OAuth client registration")

    # Run bootstrap inline via uv, using the BD venv which has pymongo + werkzeug.
    uv_bin = shutil.which("uv") or packages.UV_BIN
    bootstrap_script = os.path.join(DEPLOY_DIR, "bootstrap_bare.py")
    proc.run(
        [uv_bin, "run", "python3", bootstrap_script, *argv],
        cwd=REPO_ROOT,
    )


def print_next_steps() -> None:
    log.info("BuildingDepot is up. Next steps:")
    log.step("")
    log.step("1. Put HTTPS in front (root, once per host):")
    log.step("   sudo python3 deploy/shared/host.py install")
    log.step("   sudo python3 deploy/shared/host.py enable deploy/nginx/buildingdepot.conf \\")
    log.step("        --domain <host> --cert <tailscale|http|dns-cloudflare>")
    log.step("")
    log.step("2. Enable linger so services survive logout:")
    user = os.environ.get("USER", "$USER")
    log.step(f"   sudo loginctl enable-linger {user}")
    log.step("")
    log.step("3. View logs:")
    log.step("   journalctl --user -u bd-central -f")
    log.step("   journalctl --user -u bd-data -f")
    log.step("   journalctl --user -u bd-replica -f")
    log.step("   docker compose -f deploy/compose.yml logs")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-service", action="store_true", help="skip installing systemd user units")
    parser.add_argument("--no-bootstrap", action="store_true", help="skip admin user + ds1 registration")
    parser.add_argument("--force-env", action="store_true", help="overwrite an existing .env")
    parser.add_argument("--no-ask-sudo", action="store_true", help="skip confirmation prompts before sudo")
    parser.add_argument("--dev", action="store_true", help="include mailpit SMTP catcher (dev profile)")
    args = parser.parse_args(argv)

    if args.no_ask_sudo:
        proc.set_sudo_ask(False)

    install_apt_packages()
    uv_bin = install_uv()
    uv_sync(uv_bin)
    values = provision_env(args.force_env)
    compose_up(args.dev)
    configure_valkey(values)
    configure_rabbitmq(values)
    if not args.no_service:
        install_systemd_units(uv_bin)
    if not args.no_bootstrap:
        bootstrap(values)
    print_next_steps()


if __name__ == "__main__":
    main()
