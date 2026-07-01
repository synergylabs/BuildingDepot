# vendored deploy library — do not edit here; regenerate from the deploy source.
"""Subprocess helpers with real error handling.

Wraps subprocess so every external command (apt/snap/pnpm/systemctl/docker/
nginx/openssl/tailscale/certbot) runs through one place that logs what it ran
and turns a non-zero exit into a clear error instead of a bare traceback.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from typing import Mapping, Sequence

import log


class CommandError(RuntimeError):
    """A subprocess exited non-zero (and check=True was requested)."""


def have(command: str) -> bool:
    """True if `command` is resolvable on PATH."""
    return shutil.which(command) is not None


def require_cmd(command: str, hint: str = "") -> None:
    """Abort unless `command` is on PATH."""
    if not have(command):
        suffix = f" — {hint}" if hint else ""
        log.die(f"required command not found: {command}{suffix}")


def needs_root(argv: Sequence[str]) -> bool:
    """Check if the command requires root/sudo."""
    if not argv:
        return False
    cmd = argv[0]
    if cmd in ("apt-get", "snap", "certbot", "nginx"):
        return True
    if cmd == "systemctl" and "--user" not in argv:
        return True
    if cmd == "tailscale" and len(argv) > 1 and argv[1] == "cert":
        return True
    # For file operations: if writing to or modifying system directories
    if cmd in ("mkdir", "cp", "ln", "rm", "chmod", "tee"):
        for arg in argv[1:]:
            if arg.startswith("/etc/nginx") or arg.startswith("/etc/letsencrypt"):
                return True
    return False


def run(
    argv: Sequence[str],
    *,
    check: bool = True,
    capture: bool = False,
    cwd: str | None = None,
    env: Mapping[str, str] | None = None,
    input_text: str | None = None,
    quiet: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a command.

    `capture=True` returns stdout/stderr on the result instead of streaming to
    the terminal. `check=True` (default) raises CommandError on a non-zero exit.
    """
    argv_list = list(argv)
    if os.geteuid() != 0 and needs_root(argv_list):
        full_cmd = " ".join(argv_list)
        sys.stderr.write(f"\nCommand needs root: {full_cmd}\nAuthorize sudo? [y/N]: ")
        sys.stderr.flush()
        try:
            ans = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            ans = "n"
            sys.stderr.write("\n")
            sys.stderr.flush()
        if ans in ("y", "yes"):
            argv_list = ["sudo", *argv_list]
        else:
            log.die(f"Permission denied: user rejected sudo for '{full_cmd}'")

    if not quiet:
        log.step("$ " + " ".join(argv_list))
    try:
        result = subprocess.run(
            argv_list,
            cwd=cwd,
            env=dict(env) if env is not None else None,
            input=input_text,
            text=True,
            capture_output=capture,
            check=False,
        )
    except FileNotFoundError as exc:
        raise CommandError(f"command not found: {argv[0]}") from exc
    if check and result.returncode != 0:
        detail = ""
        if capture and result.stderr:
            detail = f"\n{result.stderr.strip()}"
        raise CommandError(
            f"command failed ({result.returncode}): {' '.join(argv)}{detail}"
        )
    return result


def run_ok(argv: Sequence[str], *, cwd: str | None = None) -> bool:
    """Run a command, returning True on exit 0 and False otherwise (never raises)."""
    result = run(argv, check=False, capture=True, cwd=cwd, quiet=True)
    return result.returncode == 0
