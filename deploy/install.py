#!/usr/bin/env python3
"""Install BuildingDepot: provision the docker env, build + start the stack, and
register the admin user and data service.

Run from the repo root:

    python3 deploy/install.py                  # provision .env, build+up, bootstrap
    python3 deploy/install.py --no-bootstrap   # skip the admin/ds1 bootstrap
    python3 deploy/install.py --force-env       # re-provision docker/.env from example
    python3 deploy/install.py --no-build        # `up -d` without rebuilding the image

`.env` is provisioned from `.env.example` with fresh infra secrets generated
locally. TLS is a separate, root step handled by the host nginx — see the
commands printed at the end and docs/deployment.md.
"""

from __future__ import annotations

import argparse
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "deploy", "shared"))

import env  # noqa: E402
import log  # noqa: E402
import packages  # noqa: E402
import proc  # noqa: E402

DOCKER_DIR = os.path.join(REPO_ROOT, "deploy", "docker")
ENV_EXAMPLE = os.path.join(DOCKER_DIR, ".env.example")
ENV_DEST = os.path.join(DOCKER_DIR, ".env")
BOOTSTRAP = os.path.join(DOCKER_DIR, "bootstrap_admin.sh")

# Infra secrets generated locally on first provision.
GENERATE = ("SECRET_KEY", "MONGO_PWD", "INFLUX_PWD", "REDIS_PWD", "RABBIT_ADMIN_PWD", "RABBIT_END_PWD")


def provision_env(force: bool) -> None:
    log.info("provisioning docker/.env")
    env.provision_env(ENV_EXAMPLE, ENV_DEST, generate=GENERATE, force=force)


def compose_up(build: bool) -> None:
    packages.ensure_docker()
    argv = ["docker", "compose", "up", "-d"]
    if build:
        argv.append("--build")
    log.info("bringing up the BuildingDepot stack")
    proc.run(argv, cwd=DOCKER_DIR)


def bootstrap() -> None:
    log.info("registering admin user and ds1 data service")
    proc.run(["bash", BOOTSTRAP], cwd=DOCKER_DIR)


def print_next_steps() -> None:
    log.info("BuildingDepot is up. Next, put HTTPS in front (root, once per host):")
    log.step("sudo python3 deploy/shared/host.py install")
    log.step("sudo python3 deploy/shared/host.py enable deploy/nginx/buildingdepot.conf \\")
    log.step("     --domain <host> --cert <tailscale|letsencrypt>")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-build", action="store_true", help="`up -d` without rebuilding the image")
    parser.add_argument("--no-bootstrap", action="store_true", help="skip the admin/ds1 bootstrap")
    parser.add_argument("--force-env", action="store_true", help="overwrite an existing docker/.env")
    args = parser.parse_args(argv)

    provision_env(args.force_env)
    compose_up(build=not args.no_build)
    if not args.no_bootstrap:
        bootstrap()
    print_next_steps()


if __name__ == "__main__":
    main()
