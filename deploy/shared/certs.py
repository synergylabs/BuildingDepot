# vendored deploy library — do not edit here; regenerate from the deploy source.
"""TLS certificate provisioning for the host reverse proxy.

Three issuers, consolidated from the apps' former cert scripts:

  - tailscale     : a Let's Encrypt cert for this node's MagicDNS (*.ts.net)
                    name, validated over the tailnet — no public IP needed.
  - letsencrypt   : certbot, HTTP-01 on :80 by default, or DNS-01 via
                    `certbot_auth_args` when :80 is not publicly reachable.

Each issuer writes (or points at) a cert/key pair and returns their paths. The
proxy config (nginx.py) consumes those paths; this module never touches nginx.
"""

from __future__ import annotations

import json
import os

import log
import proc

CERT_DIR = "/etc/nginx/certs"

CERT_MODES = ("tailscale", "letsencrypt")


def _ensure_cert_dir() -> None:
    os.makedirs(CERT_DIR, exist_ok=True)


def _site_paths(site: str) -> tuple[str, str]:
    return (
        os.path.join(CERT_DIR, f"{site}.crt"),
        os.path.join(CERT_DIR, f"{site}.key"),
    )


def detect_tailscale_domain() -> str | None:
    """Return this node's MagicDNS name from `tailscale status`, or None."""
    if not proc.have("tailscale"):
        return None
    result = proc.run(
        ["tailscale", "status", "--json"], check=False, capture=True, quiet=True
    )
    if result.returncode != 0 or not result.stdout:
        return None
    try:
        status = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    name = (status.get("Self") or {}).get("DNSName") or ""
    if not name:
        domains = status.get("CertDomains") or []
        name = domains[0] if domains else ""
    return name.rstrip(".") or None


def provision_cert(
    mode: str,
    *,
    site: str,
    domain: str | None = None,
    email: str | None = None,
    certbot_auth_args: list[str] | None = None,
) -> tuple[str, str]:
    """Provision a cert for `site` using `mode`; return (cert_path, key_path)."""
    if mode == "tailscale":
        return _cert_tailscale(site, domain)
    if mode == "letsencrypt":
        return _cert_letsencrypt(domain, email, certbot_auth_args)
    log.die(f"unknown cert mode: {mode} (use one of {', '.join(CERT_MODES)})")


def _cert_tailscale(site: str, domain: str | None) -> tuple[str, str]:
    proc.require_cmd(
        "tailscale",
        "install it and run `sudo tailscale up`, then enable MagicDNS + HTTPS "
        "certificates in the tailnet admin console",
    )
    if not proc.run_ok(["tailscale", "status"]):
        log.die("tailscale is installed but this node isn't up — run `sudo tailscale up`")
    domain = domain or detect_tailscale_domain()
    if not domain:
        log.die("could not determine the tailnet domain — pass --domain explicitly")
    _ensure_cert_dir()
    cert_file, key_file = _site_paths(site)
    log.info(f"requesting a Tailscale cert for {domain}")
    proc.run(["tailscale", "cert", "--cert-file", cert_file, "--key-file", key_file, domain])
    os.chmod(key_file, 0o600)
    return cert_file, key_file


def _cert_letsencrypt(
    domain: str | None,
    email: str | None,
    certbot_auth_args: list[str] | None,
) -> tuple[str, str]:
    if not domain:
        log.die("letsencrypt needs a public --domain that resolves to this host")
    proc.require_cmd(
        "certbot",
        "apt-install certbot (and the DNS plugin if you use DNS-01), then re-run",
    )
    # HTTP-01 on :80 by default; override with DNS-01 plugin flags for NAT'd hosts.
    auth_args = certbot_auth_args if certbot_auth_args else ["--standalone"]
    argv = ["certbot", "certonly", *auth_args, "--non-interactive", "--agree-tos", "-d", domain]
    if email:
        argv += ["-m", email]
    else:
        argv += ["--register-unsafely-without-email"]
    log.info(f"obtaining a Let's Encrypt cert for {domain}")
    proc.run(argv)
    live = f"/etc/letsencrypt/live/{domain}"
    return f"{live}/fullchain.pem", f"{live}/privkey.pem"



