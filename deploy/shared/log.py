# vendored deploy library — do not edit here; regenerate from the deploy source.
"""Minimal coloured logging for the deploy tooling.

stdlib-only. Writes human-readable status to stderr so stdout stays clean for
any value a caller wants to capture. Colours are disabled automatically when
stderr is not a TTY or when NO_COLOR is set.
"""

from __future__ import annotations

import os
import sys
from typing import NoReturn

_USE_COLOR: bool = sys.stderr.isatty() and os.environ.get("NO_COLOR") is None

_RESET = "\033[0m"
_BOLD = "\033[1m"
_BLUE = "\033[34m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_GREEN = "\033[32m"


def _paint(text: str, colour: str) -> str:
    if not _USE_COLOR:
        return text
    return f"{colour}{text}{_RESET}"


def info(message: str) -> None:
    """Print a normal progress line."""
    print(_paint("==>", _BLUE) + " " + message, file=sys.stderr)


def step(message: str) -> None:
    """Print a sub-step line (indented, dimmer than info)."""
    print("    " + message, file=sys.stderr)


def ok(message: str) -> None:
    """Print a success line."""
    print(_paint("ok ", _GREEN) + " " + message, file=sys.stderr)


def warn(message: str) -> None:
    """Print a warning line."""
    print(_paint("warn", _YELLOW) + " " + message, file=sys.stderr)


def die(message: str, code: int = 1) -> NoReturn:
    """Print an error line and exit non-zero."""
    print(_paint("error", _RED + _BOLD) + " " + message, file=sys.stderr)
    raise SystemExit(code)
