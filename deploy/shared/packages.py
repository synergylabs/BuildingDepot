# vendored deploy library — do not edit here; regenerate from the deploy source.
"""Host package installation (apt / snap / node / pnpm / docker).

Every helper is idempotent: it checks whether the tool is already present before
shelling out, so re-running an install is cheap and safe. apt/snap calls need
root; the helpers say so rather than failing obscurely.
"""

from __future__ import annotations

import os
import shutil
from typing import Sequence

import log
import proc

# Node is installed as a classic snap to match the systemd units, which call
# /snap/bin/node by absolute path (the --user manager has no snap bin on PATH).
NODE_BIN = "/snap/bin/node"


def _is_root() -> bool:
    return os.geteuid() == 0


def _require_root(action: str) -> None:
    pass


def apt_install(packages: Sequence[str]) -> None:
    """Install apt packages if any are missing. No-op when all present."""
    missing = [p for p in packages if not _dpkg_installed(p)]
    if not missing:
        log.step(f"apt: already installed: {', '.join(packages)}")
        return
    proc.require_cmd("apt-get", "this helper assumes a Debian/Ubuntu host")
    _require_root(f"installing {', '.join(missing)}")
    log.info(f"apt-get install {' '.join(missing)}")
    proc.run(["apt-get", "update", "-qq"])
    proc.run(["apt-get", "install", "-y", "-qq", *missing])


def _dpkg_installed(package: str) -> bool:
    return proc.run_ok(["dpkg", "-s", package])


def ensure_snapd() -> None:
    """Make sure snapd is available (needed for the node snap)."""
    if proc.have("snap"):
        return
    apt_install(["snapd"])


def ensure_node() -> str:
    """Ensure a Node runtime exists; return the absolute node path.

    Prefers an existing `node` on PATH; otherwise installs the classic node snap
    and returns its well-known path.
    """
    existing = shutil.which("node")
    if existing:
        log.step("node: already installed")
        return existing
    if os.path.exists(NODE_BIN):
        log.step(f"node: present at {NODE_BIN}")
        return NODE_BIN
    ensure_snapd()
    _require_root("installing the node snap")
    log.info("installing node (classic snap)")
    proc.run(["snap", "install", "node", "--classic"])
    return NODE_BIN


def ensure_pnpm() -> None:
    """Ensure pnpm is available, via corepack when possible."""
    if proc.have("pnpm"):
        log.step("pnpm: already installed")
        return
    if proc.have("corepack"):
        log.info("enabling pnpm via corepack")
        proc.run(["corepack", "enable", "pnpm"])
        proc.run(["corepack", "prepare", "pnpm@latest", "--activate"])
        return
    log.die("pnpm not found and corepack unavailable — install pnpm, then re-run")


def ensure_docker() -> None:
    """Ensure docker + the compose plugin are available."""
    if proc.have("docker") and proc.run_ok(["docker", "compose", "version"]):
        log.step("docker: already installed (with compose plugin)")
        return
    log.die(
        "docker (with the compose plugin) is required and was not found — install "
        "Docker Engine + docker-compose-plugin, then re-run "
        "(https://docs.docker.com/engine/install/)"
    )
