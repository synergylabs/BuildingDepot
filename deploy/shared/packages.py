# vendored deploy library — do not edit here; regenerate from the deploy source.
"""Host package installation (apt / node / docker).

Every helper is idempotent: it checks whether the tool is already present before
shelling out, so re-running an install is cheap and safe. apt calls escalate
to sudo when needed, prompting the user for confirmation (suppress with
``proc.set_sudo_ask(False)`` or ``--no-ask-sudo`` at the CLI level).
"""

from __future__ import annotations

import os
import shutil
from typing import Sequence

import log
import proc

# Node is installed from apt (nodejs package). /usr/bin/node is the well-known
# path; the --user manager may not have it on PATH so units reference it absolutely.
NODE_BIN = "/usr/bin/node"


def apt_install(packages: Sequence[str]) -> None:
    """Install apt packages if any are missing. No-op when all present."""
    missing = [p for p in packages if not _dpkg_installed(p)]
    if not missing:
        log.step(f"apt: already installed: {', '.join(packages)}")
        return
    proc.require_cmd("apt-get", "this helper assumes a Debian/Ubuntu host")
    log.info(f"apt-get install {' '.join(missing)}")
    reason = f"installing {', '.join(missing)}"
    proc.sudo_run(["apt-get", "update", "-qq"], reason=reason)
    # Second sudo_run inherits the cached sudo credential — no double-prompt.
    proc.sudo_run(["apt-get", "install", "-y", "-qq", *missing], reason=reason, confirm=False)


def _dpkg_installed(package: str) -> bool:
    return proc.run_ok(["dpkg", "-s", package])


def ensure_node() -> str:
    """Ensure a Node runtime exists; return the absolute node path.

    Prefers an existing `node` on PATH; otherwise installs the nodejs + npm apt
    packages and returns its well-known path. npm is a separate apt package (the
    `nodejs` package only Suggests it) but the install scripts need it for
    `npm ci` / `npm run build`, so both are installed together.
    """
    existing = shutil.which("node")
    if existing:
        log.step("node: already installed")
        return existing
    if os.path.exists(NODE_BIN):
        log.step(f"node: present at {NODE_BIN}")
        return NODE_BIN
    log.info("installing nodejs + npm (apt)")
    apt_install(["nodejs", "npm"])
    return NODE_BIN



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
