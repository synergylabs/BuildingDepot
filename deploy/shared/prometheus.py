#!/usr/bin/env python3
# vendored deploy library — do not edit here; regenerate from the deploy source.
"""Host-level Prometheus CLI (run as root) — the metrics analogue of host.py.

One Prometheus runs per instrumented host, loopback-only (127.0.0.1:2080, set
via --web.listen-address in /etc/default/prometheus), and
scrapes its co-located services over loopback. Mirroring the nginx model, the
host tooling is generic and each service contributes its own pieces from its
own repo — service-specific knowledge (metric names, thresholds, ports) never
lives in the shared tooling:

  install [--expose-remote-prometheus --domain <d> --cert <mode> --basic-auth USER:PWD]
      Install Prometheus (apt) and lay down the shared base config (a file_sd
      scrape job over targets/*.yml and a rule glob over rules/*.yml). Run once
      per host. With --expose-remote-prometheus, additionally publish the
      read-only query API over HTTPS on 2443 (fragments/prometheus.conf, basic
      auth) so a Grafana on ANOTHER host can use this Prometheus as a
      datasource — a co-located Grafana reads 127.0.0.1:2080 directly and
      doesn't need it. The exposure requires the shared nginx base
      (`host.py install`) on this host.

  enable --job <name> --target <host:port> [--rules <file>] [--metrics-path <p>]
      Register a service: write targets/<job>.yml, install the service's alert
      rules as rules/<job>.yml, and reload. Run once per service; re-run after
      a rule change.

Usage from an app's vendored copy:
  sudo python3 deploy/shared/prometheus.py install
  sudo python3 deploy/shared/prometheus.py enable --job mites-backend \
      --target 127.0.0.1:9080 --rules deploy/monitoring/alerts.yml
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys

# Run-as-script: make sibling modules importable by bare name.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import certs  # noqa: E402
import env  # noqa: E402
import log  # noqa: E402
import nginx  # noqa: E402
import packages  # noqa: E402
import proc  # noqa: E402

PROM_DIR = "/etc/prometheus"
BASE_CONF = os.path.join(PROM_DIR, "prometheus.yml")
RULES_DIR = os.path.join(PROM_DIR, "rules")
TARGETS_DIR = os.path.join(PROM_DIR, "targets")

# The packaged default is 0.0.0.0:9090 — pin loopback (nothing plaintext
# crosses the network) and 2080, pairing with the 2443 HTTPS exposure the way
# every other service pairs its loopback port with its public one.
PROM_PORT = 2080
PROM_DEFAULTS = "/etc/default/prometheus"

# The remote-Grafana exposure (see fragments/prometheus.conf).
EXPOSE_SITE = "prometheus"
EXPOSE_PORT = 2443
EXPOSE_FRAGMENT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "fragments", "prometheus.conf"
)

_JOB_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def _require_root() -> None:
    if os.geteuid() != 0:
        log.die("re-run with sudo — this installs packages and edits /etc/prometheus")


def reload() -> None:
    """Reload Prometheus (SIGHUP via systemd), falling back to a restart."""
    if proc.run_ok(["systemctl", "reload", "prometheus"]):
        return
    proc.run(["systemctl", "restart", "prometheus"])


def cmd_install(args: argparse.Namespace) -> None:
    _require_root()
    packages.apt_install(["prometheus"])

    base_src = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "prometheus_base", "prometheus.yml"
    )
    if os.path.isfile(BASE_CONF):
        backup = BASE_CONF + ".pre-deploy.bak"
        if not os.path.exists(backup):
            shutil.copy2(BASE_CONF, backup)
            log.step(f"backed up existing prometheus.yml -> {backup}")
    shutil.copy(base_src, BASE_CONF)
    os.chmod(BASE_CONF, 0o644)
    log.step(f"installed {BASE_CONF}")
    os.makedirs(RULES_DIR, exist_ok=True)
    os.makedirs(TARGETS_DIR, exist_ok=True)

    # The unit's $ARGS. Owned by this tooling — an existing ARGS is replaced.
    env.update_env(
        PROM_DEFAULTS, {"ARGS": f'"--web.listen-address=127.0.0.1:{PROM_PORT}"'}
    )
    log.step(f"set --web.listen-address=127.0.0.1:{PROM_PORT} in {PROM_DEFAULTS}")

    proc.run(["systemctl", "enable", "prometheus"], check=False)
    # Restart, not reload: a listen-address change doesn't apply on SIGHUP.
    proc.run(["systemctl", "restart", "prometheus"])
    log.ok(f"prometheus running (loopback :{PROM_PORT}); register services with `enable`")

    if args.expose_remote_prometheus:
        _expose_remote_prometheus(args)


def _expose_remote_prometheus(args: argparse.Namespace) -> None:
    """Publish the query API on 2443 for a Grafana on another host."""
    if not (args.cert and args.basic_auth):
        log.die("--expose-remote-prometheus needs --cert and --basic-auth USER:PASSWORD")
    user, sep, password = args.basic_auth.partition(":")
    if not (sep and user and password):
        log.die("--basic-auth expects USER:PASSWORD")
    domain = args.domain
    if not domain and args.cert == "tailscale":
        domain = certs.detect_tailscale_domain()
    if not domain:
        log.die("--expose-remote-prometheus needs --domain (none given, no tailnet name found)")

    htpasswd = nginx.write_htpasswd(EXPOSE_SITE, user, password)
    cert_file, key_file = certs.provision_cert(args.cert, site=EXPOSE_SITE, domain=domain)
    nginx.enable_site(
        EXPOSE_FRAGMENT,
        site=EXPOSE_SITE,
        domain=domain,
        cert_file=cert_file,
        key_file=key_file,
        extra_variables={"HTPASSWD_FILE": htpasswd},
    )
    log.ok(
        f"query API published at https://{domain}:{EXPOSE_PORT}/api/v1/ (basic auth) "
        f"— open {EXPOSE_PORT}/tcp to the Grafana host"
    )


def cmd_enable(args: argparse.Namespace) -> None:
    _require_root()
    if not _JOB_NAME.match(args.job):
        log.die(f"invalid job name: {args.job} (lowercase letters, digits, - and _)")
    if not os.path.isdir(TARGETS_DIR):
        log.die(f"{TARGETS_DIR} missing — run `prometheus.py install` first")

    target_file = os.path.join(TARGETS_DIR, f"{args.job}.yml")
    lines = [
        f"- targets:\n    - {args.target}\n",
        f"  labels:\n    job: {args.job}\n",
    ]
    if args.metrics_path != "/metrics":
        lines.append(f"    __metrics_path__: {args.metrics_path}\n")
    with open(target_file, "w", encoding="utf-8") as handle:
        handle.writelines(lines)
    os.chmod(target_file, 0o644)
    log.step(f"wrote {target_file} ({args.target})")

    if args.rules:
        if not os.path.isfile(args.rules):
            log.die(f"rules file not found: {args.rules}")
        if proc.have("promtool") and not proc.run_ok(["promtool", "check", "rules", args.rules]):
            proc.run(["promtool", "check", "rules", args.rules], check=False)
            log.die("promtool rejected the rules — not installing them")
        dest = os.path.join(RULES_DIR, f"{args.job}.yml")
        shutil.copy(args.rules, dest)
        os.chmod(dest, 0o644)
        log.step(f"installed rules -> {dest}")

    reload()
    log.ok(f"service {args.job} registered")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prometheus.py", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_install = sub.add_parser("install", help="install prometheus + shared base config")
    p_install.add_argument(
        "--expose-remote-prometheus",
        action="store_true",
        help=f"also publish the read-only query API over HTTPS on {EXPOSE_PORT} "
        "for a Grafana on another host (needs the nginx base from host.py install)",
    )
    p_install.add_argument("--domain", help="exposure hostname (default: the tailnet name)")
    p_install.add_argument("--cert", choices=certs.CERT_MODES, help="exposure certificate issuer")
    p_install.add_argument(
        "--basic-auth",
        metavar="USER:PASSWORD",
        help="exposure credentials — the pair the remote Grafana datasource authenticates with",
    )
    p_install.set_defaults(func=cmd_install)

    p_enable = sub.add_parser("enable", help="register a service (target + rules)")
    p_enable.add_argument("--job", required=True, help="job label (the service name)")
    p_enable.add_argument("--target", required=True, help="scrape target, host:port (loopback)")
    p_enable.add_argument("--rules", help="path to the service's alert-rules file")
    p_enable.add_argument("--metrics-path", default="/metrics", help="metrics path (default /metrics)")
    p_enable.set_defaults(func=cmd_enable)
    return parser


def main(argv: "list[str] | None" = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
