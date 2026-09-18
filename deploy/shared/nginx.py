# vendored deploy library — do not edit here; regenerate from the deploy source.
"""Host nginx: install the shared base config and enable per-app site fragments.

The host runs one nginx that terminates TLS for every co-located Mites service.
`install_base` lays down the shared base `nginx.conf` + `conf.d/` snippets (the
websocket map, ssl params, common proxy headers, CORS) once per host.
`enable_site` renders an app's site fragment (substituting the domain and cert
paths), symlinks it into `sites-enabled/`, tests, and reloads.

A site fragment is plain nginx with `{{ }}` placeholders for `{{ DOMAIN }}`,
`{{ SSL_CERT }}`, `{{ SSL_KEY }}` — plus `{{ HTPASSWD_FILE }}` in fragments
gated by HTTP basic auth (`host.py enable --basic-auth` supplies it via
`write_htpasswd`) — and nothing else templated, so nginx's own
`$host`/`$connection_upgrade`/… survive verbatim.
"""

from __future__ import annotations

import os
import shutil
from typing import Mapping

import log
import proc
import template

NGINX_ROOT = "/etc/nginx"
SITES_AVAILABLE = os.path.join(NGINX_ROOT, "sites-available")
SITES_ENABLED = os.path.join(NGINX_ROOT, "sites-enabled")
CONF_D = os.path.join(NGINX_ROOT, "conf.d")
HTPASSWD_DIR = os.path.join(NGINX_ROOT, "htpasswd")


def install_nginx() -> None:
    """Install nginx (apt) if missing and make sure it's enabled."""
    if proc.have("nginx"):
        log.step("nginx: already installed")
    else:
        import packages

        packages.apt_install(["nginx"])
    proc.run(["systemctl", "enable", "--now", "nginx"], check=False)


def install_base(base_dir: str) -> None:
    """Install the shared base config from `base_dir` (the vendored nginx_base/).

    Backs up an existing top-level nginx.conf, then installs ours plus the
    conf.d/ snippets and ensures sites-available/ + sites-enabled/ exist.
    """
    src_conf = os.path.join(base_dir, "nginx.conf")
    src_confd = os.path.join(base_dir, "conf.d")
    if not os.path.isfile(src_conf):
        log.die(f"base nginx.conf not found at {src_conf}")

    os.makedirs(SITES_AVAILABLE, exist_ok=True)
    os.makedirs(SITES_ENABLED, exist_ok=True)
    os.makedirs(CONF_D, exist_ok=True)

    dest_conf = os.path.join(NGINX_ROOT, "nginx.conf")
    if os.path.isfile(dest_conf):
        backup = dest_conf + ".pre-deploy.bak"
        if not os.path.exists(backup):
            shutil.copy2(dest_conf, backup)
            log.step(f"backed up existing nginx.conf -> {backup}")
    shutil.copy2(src_conf, dest_conf)
    log.step(f"installed {dest_conf}")

    for name in sorted(os.listdir(src_confd)):
        if name.endswith(".conf"):
            shutil.copy2(os.path.join(src_confd, name), os.path.join(CONF_D, name))
            log.step(f"installed conf.d/{name}")

    nginx_test()
    reload()
    log.ok("base nginx config installed")


def write_htpasswd(site: str, user: str, password: str) -> str:
    """Write an htpasswd file for `site` and return its path.

    The hash is apr1 (via openssl), which nginx's `auth_basic_user_file`
    accepts. The file must be readable by the nginx workers, so it is group
    www-data mode 640 (falling back to 644 with a warning when that group
    doesn't exist).
    """
    proc.require_cmd("openssl", "needed to hash the basic-auth password")
    os.makedirs(HTPASSWD_DIR, exist_ok=True)
    path = os.path.join(HTPASSWD_DIR, site)
    # -stdin keeps the password out of the process list.
    result = proc.run(
        ["openssl", "passwd", "-apr1", "-stdin"],
        capture=True,
        quiet=True,
        input_text=password + "\n",
    )
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o640)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(f"{user}:{result.stdout.strip()}\n")
    try:
        shutil.chown(path, group="www-data")
        os.chmod(path, 0o640)
    except (LookupError, PermissionError):
        os.chmod(path, 0o644)
        log.warn(f"no www-data group — {path} left world-readable (hash only)")
    log.step(f"wrote basic-auth file {path} (user {user})")
    return path


def enable_site(
    fragment_path: str,
    *,
    site: str,
    domain: str,
    cert_file: str,
    key_file: str,
    extra_variables: Mapping[str, str] | None = None,
) -> None:
    """Render and enable an app's site fragment, then test + reload nginx."""
    if not os.path.isfile(fragment_path):
        log.die(f"site fragment not found: {fragment_path}")
    os.makedirs(SITES_AVAILABLE, exist_ok=True)
    os.makedirs(SITES_ENABLED, exist_ok=True)

    available = os.path.join(SITES_AVAILABLE, site)
    enabled = os.path.join(SITES_ENABLED, site)

    if os.path.isfile(available):
        backup = f"{available}.bak"
        shutil.copy2(available, backup)
        log.step(f"backed up existing site -> {backup}")

    variables: dict[str, str] = {
        "DOMAIN": domain,
        "SSL_CERT": cert_file,
        "SSL_KEY": key_file,
        **(extra_variables or {}),
    }
    rendered = template.render(_read(fragment_path), variables)
    with open(available, "w", encoding="utf-8") as handle:
        handle.write(rendered)
    if os.path.islink(enabled) or os.path.exists(enabled):
        os.remove(enabled)
    os.symlink(available, enabled)
    log.step(f"enabled site {site} -> {domain}")

    nginx_test()
    reload()
    log.ok(f"site {site} enabled for {domain}")


def nginx_test() -> None:
    """Run `nginx -t`, aborting on failure."""
    if not proc.run_ok(["nginx", "-t"]):
        proc.run(["nginx", "-t"], check=False)  # re-run so the operator sees why
        log.die("nginx config test failed — not reloading")


def reload() -> None:
    """Reload nginx, falling back to a restart if reload isn't possible."""
    if proc.run_ok(["systemctl", "reload", "nginx"]):
        return
    proc.run(["systemctl", "restart", "nginx"])


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()
