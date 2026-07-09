# vendored deploy library — do not edit here; regenerate from the deploy source.
"""Grafana on the host: native install and configuration, authentication included.

Grafana installs from Grafana's own apt repository (the Ubuntu archive doesn't
carry it) and is configured exclusively through `GF_*` environment variables in
/etc/default/grafana-server — the packaged systemd unit loads that file, and
GF_ variables override grafana.ini, so the package's own config file is never
edited and survives upgrades untouched.

`server_settings` and `auth_settings` build the variable sets for the two
things a deployment must pin down: where Grafana listens (loopback behind the
host reverse proxy, with its public `root_url`) and who can get in (the admin
login, sign-up off, optional anonymous read-only viewing). `configure` merges
them into the defaults file; `restart` makes them take effect.

Caveat: `GF_SECURITY_ADMIN_PASSWORD` seeds the admin account only on Grafana's
FIRST start — once the database exists it wins. Use `reset_admin_password` to
change the login on an already-initialised install.

Everything here needs root.
"""

from __future__ import annotations

import os
import urllib.request
from typing import Mapping

import env
import log
import packages
import proc

APT_KEY_URL = "https://apt.grafana.com/gpg.key"
APT_KEYRING = "/etc/apt/keyrings/grafana.gpg"
APT_LIST = "/etc/apt/sources.list.d/grafana.list"
DEFAULTS_FILE = "/etc/default/grafana-server"
SERVICE = "grafana-server"


def install() -> None:
    """Install Grafana from its apt repo. No-op when already installed."""
    if proc.run_ok(["dpkg", "-s", "grafana"]):
        log.step("grafana: already installed")
        return
    _ensure_apt_repo()
    packages.apt_install(["grafana"])


def _ensure_apt_repo() -> None:
    proc.require_cmd("gpg", "needed to dearmor the Grafana apt signing key")
    if not os.path.exists(APT_KEYRING):
        log.info(f"adding the Grafana apt repo ({APT_KEY_URL})")
        os.makedirs(os.path.dirname(APT_KEYRING), exist_ok=True)
        with urllib.request.urlopen(APT_KEY_URL) as response:
            armored = response.read().decode("utf-8")
        proc.run(["gpg", "--dearmor", "-o", APT_KEYRING], input_text=armored, quiet=True)
    with open(APT_LIST, "w", encoding="utf-8") as handle:
        handle.write(f"deb [signed-by={APT_KEYRING}] https://apt.grafana.com stable main\n")


def server_settings(
    *,
    http_addr: str = "127.0.0.1",
    http_port: int = 3000,
    root_url: str | None = None,
    serve_from_sub_path: bool = False,
) -> dict[str, str]:
    """GF_ variables pinning where Grafana listens and its public URL.

    The loopback default matches the deployment model everywhere else: the app
    never terminates TLS itself, the host nginx fronts it. `root_url` is the
    public URL the proxy serves Grafana at (needed for correct redirect and
    asset URLs); `serve_from_sub_path` only when that URL has a path component.
    """
    settings = {
        "GF_SERVER_HTTP_ADDR": http_addr,
        "GF_SERVER_HTTP_PORT": str(http_port),
        "GF_SERVER_SERVE_FROM_SUB_PATH": "true" if serve_from_sub_path else "false",
    }
    if root_url:
        settings["GF_SERVER_ROOT_URL"] = root_url
    return settings


def auth_settings(
    *,
    admin_user: str = "admin",
    admin_password: str,
    allow_sign_up: bool = False,
    anonymous_viewer: bool = False,
) -> dict[str, str]:
    """GF_ variables for who can get in.

    `admin_password` seeds the admin account on first start only (see the
    module docstring). `anonymous_viewer=True` opens read-only dashboard
    viewing without a login — only sensible on a private network / tailnet.
    """
    settings = {
        "GF_SECURITY_ADMIN_USER": admin_user,
        "GF_SECURITY_ADMIN_PASSWORD": admin_password,
        "GF_USERS_ALLOW_SIGN_UP": "true" if allow_sign_up else "false",
        "GF_AUTH_ANONYMOUS_ENABLED": "true" if anonymous_viewer else "false",
    }
    if anonymous_viewer:
        settings["GF_AUTH_ANONYMOUS_ORG_ROLE"] = "Viewer"
    return settings


def configure(settings: Mapping[str, str]) -> None:
    """Merge GF_ variables into the defaults file (kept chmod 600 — it holds
    the admin password)."""
    env.update_env(DEFAULTS_FILE, settings)
    log.step(f"updated {DEFAULTS_FILE} ({', '.join(sorted(settings))})")


def restart() -> None:
    """Enable and (re)start grafana-server so new settings take effect."""
    proc.run(["systemctl", "enable", SERVICE], check=False)
    proc.run(["systemctl", "restart", SERVICE])


def reset_admin_password(password: str) -> None:
    """Reset the admin password on an already-initialised Grafana."""
    proc.require_cmd("grafana-cli", "install grafana first")
    log.info("resetting the Grafana admin password (grafana-cli)")
    # quiet + capture keep the password out of the step log and the terminal.
    proc.run(
        ["grafana-cli", "admin", "reset-admin-password", password],
        quiet=True,
        capture=True,
    )
    log.ok("admin password reset")
