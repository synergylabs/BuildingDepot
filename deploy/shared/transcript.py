# vendored deploy library — do not edit here; regenerate from the deploy source.
"""Tee everything the process prints — its own output and its children's — to a file.

A deploy run is mostly other people's output: apt, npm, uv, docker, certbot. Those
write to an inherited *file descriptor*, not through any Python object, so wrapping
`sys.stdout` would capture our own `log` lines and none of the interesting ones. The
redirect therefore happens at the fd level: fds 1 and 2 are pointed at pipes, and a
thread per pipe forwards each line to both the original terminal and the log file.

Secrets are masked once, in that forwarding step, so a registered value cannot reach
either destination. That is deliberately the only masking mechanism — callers do not
have to remember to redact at each call site, and there is no second implementation
to keep in step with this one. Register values with `redact()` as early as they are
known; anything not registered is written verbatim.

Two consequences of owning fds 1 and 2 that callers should know about:

  * `sys.stderr.isatty()` is False for the rest of the run. `log` decides its
    colours at import time, before this runs, so it is unaffected — but any *new*
    TTY check in this library will read as "not a terminal" under a transcript.
  * Terminal output becomes line-buffered, so a partial line without a newline is
    held until it is finished. Anything that must appear immediately has to bypass
    the pipe by writing to /dev/tty, which is what `prompt` does and what sudo
    already does for its password prompt.
"""

from __future__ import annotations

import atexit
import os
import re
import sys
import threading
from typing import Iterable

_MASK = "***"

# CSI escape sequences (colour, cursor moves). Stripped from the file copy only, so
# the log is plain text while the terminal keeps its colours.
_ANSI = re.compile(rb"\x1b\[[0-9;]*[A-Za-z]")

_secrets: list[bytes] = []
_lock = threading.Lock()

_path: str | None = None
_file_fd: int | None = None
_saved: dict[int, int] = {}
_threads: list[threading.Thread] = []


def redact(values: Iterable[str]) -> None:
    """Mask these values in everything written from now on.

    Longest first, so a secret that contains another secret as a substring is
    replaced whole rather than leaving a fragment behind.
    """
    with _lock:
        for value in values:
            # Short values would mask half the log; blank ones would mask all of it.
            if value and len(value) >= 8:
                _secrets.append(value.encode())
        _secrets.sort(key=len, reverse=True)


def _scrub(line: bytes) -> bytes:
    with _lock:
        secrets = list(_secrets)
    for secret in secrets:
        line = line.replace(secret, _MASK.encode())
    return line


def path() -> str | None:
    """The active transcript's path, or None when no transcript is running."""
    return _path


def _pump(read_fd: int, tty_fd: int) -> None:
    """Forward one pipe to the terminal and the log until it closes.

    Lines rather than raw chunks because a secret split across two reads could not be
    matched otherwise — which is also why this cannot just be `tee`.
    """
    buffered = b""
    while True:
        try:
            chunk = os.read(read_fd, 4096)
        except OSError:
            break
        if not chunk:
            break
        buffered += chunk
        while b"\n" in buffered:
            line, buffered = buffered.split(b"\n", 1)
            _emit(line + b"\n", tty_fd)
    if buffered:
        _emit(buffered, tty_fd)


def _emit(line: bytes, tty_fd: int) -> None:
    clean = _scrub(line)
    _write_all(tty_fd, clean)
    if _file_fd is not None:
        with _lock:
            _write_all(_file_fd, _ANSI.sub(b"", clean))


def _write_all(fd: int, data: bytes) -> None:
    """os.write may write short; a partial status line is worse than none."""
    while data:
        try:
            written = os.write(fd, data)
        except OSError:
            return
        data = data[written:]


def start(dest: str, *, append: bool = True) -> None:
    """Begin teeing fds 1 and 2 to *dest*.

    The log is opened 0600: even with secrets masked, a deploy transcript is a full
    description of the host's configuration.
    """
    global _path, _file_fd
    if _path is not None:
        raise RuntimeError(f"a transcript is already running: {_path}")

    sys.stdout.flush()
    sys.stderr.flush()

    flags = os.O_WRONLY | os.O_CREAT | (os.O_APPEND if append else os.O_TRUNC)
    _file_fd = os.open(dest, flags, 0o600)
    _path = dest

    # One pipe per stream rather than one shared pipe, so stdout and stderr stay
    # separable on the terminal — log.py keeps stdout clean for captured values, and
    # that promise should survive being teed.
    for target in (1, 2):
        _saved[target] = os.dup(target)
        read_fd, write_fd = os.pipe()
        os.dup2(write_fd, target)
        os.close(write_fd)
        thread = threading.Thread(
            target=_pump, args=(read_fd, _saved[target]), daemon=True
        )
        thread.start()
        _threads.append(thread)

    atexit.register(stop)


def stop() -> None:
    """Restore fds 1 and 2, drain the pumps, and close the log. Safe to call twice."""
    global _path, _file_fd
    if _path is None:
        return

    sys.stdout.flush()
    sys.stderr.flush()

    # Restoring the saved fd onto 1/2 drops the last reference to the pipe's write
    # end, which is what lets the pump see EOF and finish.
    for target, saved_fd in _saved.items():
        os.dup2(saved_fd, target)

    # Join before closing the saved fds, not after: a pump still draining the last
    # lines writes to its saved fd, and closing it first silently loses that output.
    for thread in _threads:
        # Bounded: a stray descendant holding the pipe open should not hang exit.
        thread.join(timeout=2.0)
    _threads.clear()

    for saved_fd in _saved.values():
        os.close(saved_fd)
    _saved.clear()

    if _file_fd is not None:
        os.close(_file_fd)
    _file_fd = None
    _path = None
