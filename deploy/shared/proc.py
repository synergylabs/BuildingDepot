# vendored deploy library — do not edit here; regenerate from the deploy source.
"""Subprocess helpers with real error handling.

Wraps subprocess so every external command (apt/snap/systemctl/docker/
nginx/openssl/tailscale/certbot) runs through one place that logs what it ran
and turns a non-zero exit into a clear error instead of a bare traceback.
"""

from __future__ import annotations

import shutil
import subprocess
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
    if not quiet:
        log.step("$ " + " ".join(argv))
    try:
        result = subprocess.run(
            list(argv),
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

