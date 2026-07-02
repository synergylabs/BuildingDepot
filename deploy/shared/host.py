#!/usr/bin/env python3
# vendored deploy library — do not edit here; regenerate from the deploy source.
"""Host-level reverse-proxy CLI (run as root).

Two subcommands, both operating on the one nginx that fronts every co-located service:

  install
      Install nginx and lay down the shared base config (nginx.conf + conf.d/).
      Run once per host.

  enable <fragment> --domain <d> --cert <mode> [...]
      Provision a TLS cert and enable an app's site fragment. Run once per app.
      Cert modes: tailscale | letsencrypt.

Usage from any app's vendored copy:
  sudo python3 deploy/shared/host.py install
  sudo python3 deploy/shared/host.py enable deploy/nginx/<app>.conf.sample \
      --domain host.tailnet.ts.net --cert tailscale
"""

from __future__ import annotations

import argparse
import os
import sys

# Run-as-script: make sibling modules importable by bare name.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import certs  # noqa: E402
import log  # noqa: E402
import nginx  # noqa: E402


def _require_root() -> None:
    if os.geteuid() != 0:
        log.die("re-run with sudo — this edits /etc/nginx and runs cert tooling")


def _default_site_name(fragment_path: str) -> str:
    base = os.path.basename(fragment_path)
    for suffix in (".conf.sample", ".conf", ".sample"):
        if base.endswith(suffix):
            return base[: -len(suffix)]
    return base


def cmd_install(_: argparse.Namespace) -> None:
    _require_root()
    nginx.install_nginx()
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nginx_base")
    nginx.install_base(base_dir)


def cmd_enable(args: argparse.Namespace) -> None:
    _require_root()
    site = args.site or _default_site_name(args.fragment)
    cert_file, key_file = certs.provision_cert(
        args.cert,
        site=site,
        domain=args.domain,
        email=args.email,
        certbot_auth_args=args.certbot_auth_arg or None,
    )
    nginx.enable_site(
        args.fragment,
        site=site,
        domain=args.domain or "",
        cert_file=cert_file,
        key_file=key_file,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="host.py", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_install = sub.add_parser("install", help="install nginx + shared base config")
    p_install.set_defaults(func=cmd_install)

    p_enable = sub.add_parser("enable", help="provision a cert + enable a site fragment")
    p_enable.add_argument("fragment", help="path to the app's nginx site fragment")
    p_enable.add_argument("--domain", help="server_name / cert domain")
    p_enable.add_argument(
        "--cert",
        required=True,
        choices=certs.CERT_MODES,
        help="certificate issuer",
    )
    p_enable.add_argument("--site", help="site name (defaults to the fragment filename)")

    p_enable.add_argument("--email", help="letsencrypt: contact email")
    p_enable.add_argument(
        "--certbot-auth-arg",
        action="append",
        help="letsencrypt: extra certbot authenticator arg (repeatable, e.g. for DNS-01)",
    )
    p_enable.set_defaults(func=cmd_enable)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
