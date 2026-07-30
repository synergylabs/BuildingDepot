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

# uv is installed via pipx (not in apt). pipx always installs per-user into
# ~/.local/bin regardless of who invokes it, so this is the well-known path;
# units reference it absolutely (like NODE_BIN above).
UV_BIN = os.path.expanduser("~/.local/bin/uv")


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



def ensure_uv() -> str:
    """Ensure a uv Python package manager exists; return the absolute path.

    Prefers an existing ``uv`` on PATH; otherwise installs pipx from apt (a
    system package, needs sudo once) and uses it to install uv into the
    current user's ``~/.local/bin`` (no sudo — pipx installs are always
    per-user, never system-wide).

    Snap was tried and ruled out empirically: the only uv snap available
    (``astral-uv``) is an unofficial third-party repackaging (publisher
    "lengau", not astral-sh) and uses classic confinement, which hits the
    same AppArmor profile-transition bug as the Node snap (LP #1849753) —
    stdout silently vanishes when redirected under systemd. Verified: `uv
    --version` under a unit with `StandardOutput=journal` exited 0 and wrote
    zero bytes. pipx's install has no confinement wrapper and was verified to
    work under the same conditions.
    """
    existing = shutil.which("uv")
    if existing:
        log.step("uv: already installed")
        return existing
    if os.path.exists(UV_BIN):
        log.step(f"uv: present at {UV_BIN}")
        return UV_BIN
    log.info("installing uv via pipx")
    apt_install(["pipx"])
    proc.run(["pipx", "install", "uv"])
    if not os.path.exists(UV_BIN):
        log.die(f"pipx installed uv but {UV_BIN} not found — check pipx's bin location")
    return UV_BIN


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
