# vendored deploy library — do not edit here; regenerate from the deploy source.
"""TLS certificate provisioning for the host reverse proxy.

Three issuers, consolidated from the apps' former cert scripts:

  - tailscale       : a Let's Encrypt cert for this node's MagicDNS (*.ts.net)
                      name, validated over the tailnet — no public IP needed.
  - http            : certbot, HTTP-01 on :80 by default. Needs a public IP and
                      a domain whose A/AAAA record points at this host.
                      (`letsencrypt` is accepted as a legacy alias.)
  - dns-cloudflare  : certbot + the dns-cloudflare plugin, DNS-01 via the
                      Cloudflare API. Works behind NAT/CGNAT — no inbound port
                      needed. Requires a Cloudflare API token.

certbot (and the DNS plugin when needed) is installed via apt on first use.

Each issuer writes (or points at) a cert/key pair and returns their paths. The
proxy config (nginx.py) consumes those paths; this module never touches nginx.
"""

from __future__ import annotations

import json
import os

import log
import packages
import proc

CERT_DIR = "/etc/nginx/certs"

CERT_MODES = ("tailscale", "http", "dns-cloudflare")
_LEGACY_ALIASES: dict[str, str] = {"letsencrypt": "http"}

_CF_CREDENTIALS_PATH = "/etc/letsencrypt/cloudflare.ini"


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
    cloudflare_token: str | None = None,
) -> tuple[str, str]:
    """Provision a cert for `site` using `mode`; return (cert_path, key_path)."""
    mode = _LEGACY_ALIASES.get(mode, mode)
    if mode == "tailscale":
        return _cert_tailscale(site, domain)
    if mode == "http":
        return _cert_http(domain, email, certbot_auth_args)
    if mode == "dns-cloudflare":
        return _cert_dns_cloudflare(domain, email, cloudflare_token)
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


def _cert_http(
    domain: str | None,
    email: str | None,
    certbot_auth_args: list[str] | None,
) -> tuple[str, str]:
    if not domain:
        log.die("http cert mode needs a public --domain that resolves to this host")
    packages.apt_install(["certbot"])
    # HTTP-01 on :80 by default; override with custom authenticator flags.
    auth_args = certbot_auth_args if certbot_auth_args else ["--standalone"]
    argv = ["certbot", "certonly", *auth_args, "--non-interactive", "--agree-tos", "-d", domain]
    if email:
        argv += ["-m", email]
    else:
        argv += ["--register-unsafely-without-email"]
    log.info(f"obtaining a Let's Encrypt cert for {domain} (HTTP-01)")
    proc.run(argv)
    return _letsencrypt_paths(domain)


def _cert_dns_cloudflare(
    domain: str | None,
    email: str | None,
    cloudflare_token: str | None,
) -> tuple[str, str]:
    if not domain:
        log.die("dns-cloudflare cert mode needs --domain")
    token = cloudflare_token or os.environ.get("CF_DNS_API_TOKEN")
    if not token:
        log.die(
            "dns-cloudflare needs a Cloudflare API token — pass --cloudflare-token "
            "or set the CF_DNS_API_TOKEN environment variable"
        )
    packages.apt_install(["certbot", "python3-certbot-dns-cloudflare"])
    _write_cf_credentials(token)
    argv = [
        "certbot", "certonly",
        "--dns-cloudflare",
        "--dns-cloudflare-credentials", _CF_CREDENTIALS_PATH,
        "--non-interactive", "--agree-tos",
        "-d", domain,
    ]
    if email:
        argv += ["-m", email]
    else:
        argv += ["--register-unsafely-without-email"]
    log.info(f"obtaining a Let's Encrypt cert for {domain} (DNS-01 via Cloudflare)")
    proc.run(argv)
    return _letsencrypt_paths(domain)


def _write_cf_credentials(token: str) -> None:
    """Write the Cloudflare credentials .ini for certbot (chmod 600)."""
    os.makedirs(os.path.dirname(_CF_CREDENTIALS_PATH), exist_ok=True)
    fd = os.open(_CF_CREDENTIALS_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(f"dns_cloudflare_api_token = {token}\n")
    log.step(f"wrote Cloudflare credentials to {_CF_CREDENTIALS_PATH}")


def _letsencrypt_paths(domain: str) -> tuple[str, str]:
    """Return the cert/key paths under /etc/letsencrypt/live/."""
    live = f"/etc/letsencrypt/live/{domain}"
    return f"{live}/fullchain.pem", f"{live}/privkey.pem"
