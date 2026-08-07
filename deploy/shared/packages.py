# vendored deploy library — do not edit here; regenerate from the deploy source.
"""Host package installation (apt / node / docker).

Every helper is idempotent: it checks whether the tool is already present before
shelling out, so re-running an install is cheap and safe. apt calls escalate
to sudo when needed, prompting the user for confirmation (suppress with
``proc.set_sudo_ask(False)`` or ``--no-ask-sudo`` at the CLI level).
"""

from __future__ import annotations

import getpass
import grp
import os
import pwd
import shutil
import subprocess
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

# None until the docker socket has been probed; see `docker_argv`.
_docker_needs_sudo: bool | None = None


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
    """Ensure docker + the compose plugin are available; install from apt if not.

    Uses the distro packages — ``docker.io`` (the engine) and
    ``docker-compose-v2`` (the ``docker compose`` CLI plugin) — rather than
    Docker's own apt repo: no third-party source or signing key to manage, and
    updates arrive with the release's security pocket. An existing Docker
    Engine install from docker.com already satisfies the check and is left
    alone. ``docker-compose-v2`` exists on Ubuntu 23.10+ and Debian 13+; older
    releases only ship the standalone v1 ``docker-compose``, which the compose
    calls here do not use.
    """
    if proc.have("docker") and proc.run_ok(["docker", "compose", "version"]):
        log.step("docker: already installed (with compose plugin)")
    else:
        log.info("installing docker.io + docker-compose-v2 (apt)")
        apt_install(["docker.io", "docker-compose-v2"])
        if not (proc.have("docker") and proc.run_ok(["docker", "compose", "version"])):
            log.die(
                "installed docker.io + docker-compose-v2 but `docker compose` still "
                "does not work — this host's release may predate the compose v2 "
                "plugin package; install Docker Engine + docker-compose-plugin "
                "instead (https://docs.docker.com/engine/install/)"
            )
    _ensure_docker_access()


def _ensure_docker_access() -> None:
    """Ensure this process can reach the docker daemon, directly or via sudo.

    A fresh ``docker.io`` install leaves the socket owned by ``root:docker``, so
    the first non-root run cannot reach it. The user is added to the ``docker``
    group for future runs, but group membership only applies to a new login
    session — so this run keeps going with sudo instead of stopping to make the
    operator log out mid-install. Callers must go through :func:`docker_run` /
    :func:`docker_argv` for that fallback to apply.
    """
    global _docker_needs_sudo
    if proc.run_ok(["docker", "info"]):
        _docker_needs_sudo = False
        return
    if os.geteuid() == 0:
        log.die("docker is installed but the daemon is not reachable — check `systemctl status docker`")

    user = getpass.getuser()
    if not _in_group(user, "docker"):
        log.warn(
            f"{user} cannot reach the docker socket. Adding {user} to the `docker` group "
            "grants full control of the docker daemon, which is equivalent to root on this host."
        )
        proc.sudo_run(["usermod", "-aG", "docker", user], reason="grant access to the docker socket")

    # Whether the group was added just now or by an earlier run, this session
    # does not carry it yet — verify the daemon answers under sudo, so a dead
    # daemon is reported here rather than as a confusing compose failure later.
    probe = proc.sudo_run(["docker", "info"], confirm=False, check=False, capture=True)
    if probe.returncode != 0:
        log.die("docker daemon is not reachable even as root — check `systemctl status docker`")
    _docker_needs_sudo = True
    log.step(
        f"docker: running docker via sudo for this run — {user} is in the `docker` group "
        "but the membership only applies after a new login (or `newgrp docker`)"
    )


def docker_needs_sudo() -> bool:
    """Whether docker calls from this process have to go through sudo.

    Probes the socket on first use so callers that never went through
    :func:`ensure_docker` (status/reporting tools) behave the same way.
    """
    global _docker_needs_sudo
    if _docker_needs_sudo is None:
        # `proc.have` first: run_ok raises on a missing binary, and a host with
        # no docker at all should fail on the real call, not on this probe.
        _docker_needs_sudo = (
            os.geteuid() != 0 and proc.have("docker") and not proc.run_ok(["docker", "info"])
        )
    return _docker_needs_sudo


def docker_argv(*args: str) -> list[str]:
    """The argv for a docker command, sudo-prefixed when the socket needs it."""
    prefix = ["sudo", "docker"] if docker_needs_sudo() else ["docker"]
    return [*prefix, *args]


def docker_run(
    args: Sequence[str],
    *,
    reason: str = "run docker",
    check: bool = True,
    capture: bool = False,
    cwd: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run ``docker <args>``, escalating to sudo when the socket is not reachable."""
    argv = ["docker", *args]
    if docker_needs_sudo():
        return proc.sudo_run(argv, reason=reason, confirm=False, check=check, capture=capture, cwd=cwd)
    return proc.run(argv, check=check, capture=capture, cwd=cwd)


def _in_group(user: str, group: str) -> bool:
    """True if *user* would have *group* in a fresh login session."""
    try:
        gid = grp.getgrnam(group).gr_gid
    except KeyError:
        return False
    return gid in os.getgrouplist(user, pwd.getpwnam(user).pw_gid)
