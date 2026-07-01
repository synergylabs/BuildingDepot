# vendored deploy library — do not edit here; regenerate from the deploy source.
"""Host nginx: install the shared base config and enable per-app site fragments.

The host runs one nginx that terminates TLS for every co-located service.
`install_base` lays down the shared base `nginx.conf` + `conf.d/` snippets (the
websocket map, ssl params, common proxy headers, CORS) once per host.
`enable_site` renders an app's site fragment (substituting the domain and cert
paths), symlinks it into `sites-enabled/`, tests, and reloads.

A site fragment is plain nginx with three `{{ }}` placeholders — `{{ DOMAIN }}`,
`{{ SSL_CERT }}`, `{{ SSL_KEY }}` — and nothing else templated, so nginx's own
`$host`/`$connection_upgrade`/… survive verbatim.
"""

from __future__ import annotations

import os
import shutil

import log
import proc
import template

NGINX_ROOT = "/etc/nginx"
SITES_AVAILABLE = os.path.join(NGINX_ROOT, "sites-available")
SITES_ENABLED = os.path.join(NGINX_ROOT, "sites-enabled")
CONF_D = os.path.join(NGINX_ROOT, "conf.d")


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

    proc.run(["mkdir", "-p", SITES_AVAILABLE])
    proc.run(["mkdir", "-p", SITES_ENABLED])
    proc.run(["mkdir", "-p", CONF_D])

    dest_conf = os.path.join(NGINX_ROOT, "nginx.conf")
    if os.path.isfile(dest_conf):
        backup = dest_conf + ".pre-deploy.bak"
        if not os.path.exists(backup):
            proc.run(["cp", "-p", dest_conf, backup])
            log.step(f"backed up existing nginx.conf -> {backup}")
    proc.run(["cp", "-p", src_conf, dest_conf])
    log.step(f"installed {dest_conf}")

    for name in sorted(os.listdir(src_confd)):
        if name.endswith(".conf"):
            proc.run(["cp", "-p", os.path.join(src_confd, name), os.path.join(CONF_D, name)])
            log.step(f"installed conf.d/{name}")

    nginx_test()
    reload()
    log.ok("base nginx config installed")


def enable_site(
    fragment_path: str,
    *,
    site: str,
    domain: str,
    cert_file: str,
    key_file: str,
) -> None:
    """Render and enable an app's site fragment, then test + reload nginx."""
    if not os.path.isfile(fragment_path):
        log.die(f"site fragment not found: {fragment_path}")
    proc.run(["mkdir", "-p", SITES_AVAILABLE])
    proc.run(["mkdir", "-p", SITES_ENABLED])

    available = os.path.join(SITES_AVAILABLE, site)
    enabled = os.path.join(SITES_ENABLED, site)

    if os.path.isfile(available):
        backup = f"{available}.bak"
        proc.run(["cp", "-p", available, backup])
        log.step(f"backed up existing site -> {backup}")

    rendered = template.render(
        _read(fragment_path),
        {"DOMAIN": domain, "SSL_CERT": cert_file, "SSL_KEY": key_file},
    )
    proc.run(["tee", available], input_text=rendered, capture=True, quiet=True)
    proc.run(["rm", "-f", enabled])
    proc.run(["ln", "-s", available, enabled])
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
