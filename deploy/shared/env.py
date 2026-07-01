# vendored deploy library — do not edit here; regenerate from the deploy source.
"""Reading, writing, and provisioning `.env` files.

`provision_env` is the workhorse: it copies a committed `.env.example` to a
gitignored `.env`, substituting operator-supplied overrides and generating fresh
secrets for designated keys, while preserving the example's comments and
ordering. It never overwrites an existing `.env` unless `force=True`, so it is
safe to re-run.

All files written here are chmod 600 — they hold secrets and must not be
world-readable.
"""

from __future__ import annotations

import os
import re
import secrets
from typing import Iterable, Mapping

import log

# KEY=VALUE, tolerating leading whitespace and an optional `export `.
_ASSIGN = re.compile(r"^(\s*)(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$")

# Values that mean "operator has not filled this in yet".
_PLACEHOLDER_VALUES = frozenset({"", "replace-me", "replace-me-with-openssl-rand-hex-32"})


def generate_secret(num_bytes: int = 32) -> str:
    """Return a fresh random hex secret (equivalent to `openssl rand -hex N`)."""
    return secrets.token_hex(num_bytes)


def read_env(path: str) -> dict[str, str]:
    """Parse a `.env` file into a dict. Comments and blank lines are skipped.

    Surrounding single/double quotes on values are stripped. Missing file -> {}.
    """
    values: dict[str, str] = {}
    if not os.path.exists(path):
        return values
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            match = _ASSIGN.match(line)
            if not match:
                continue
            key = match.group(2)
            raw = match.group(3).strip()
            if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ("'", '"'):
                raw = raw[1:-1]
            values[key] = raw
    return values


def write_env(path: str, values: Mapping[str, str]) -> None:
    """Write a flat `KEY=value` file (no comments) at chmod 600."""
    lines = [f"{key}={value}\n" for key, value in values.items()]
    _write_secure(path, "".join(lines))


def _write_secure(path: str, content: str) -> None:
    # Create with 0600 from the start so the secret is never briefly world-readable.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
    finally:
        # fdopen's close handles the descriptor; ensure perms even if it pre-existed.
        os.chmod(path, 0o600)


def provision_env(
    example_path: str,
    dest_path: str,
    *,
    overrides: Mapping[str, str] | None = None,
    generate: Iterable[str] = (),
    force: bool = False,
) -> bool:
    """Create `dest_path` from `example_path`, preserving comments and order.

    - `overrides`: KEY -> value applied to matching assignment lines.
    - `generate`: keys whose value is filled with a fresh secret *only when* the
      example's value is still a placeholder and no override was supplied.
    - Existing `dest_path` is left untouched unless `force=True`.

    Returns True if it wrote the file, False if it skipped an existing one.
    """
    overrides = dict(overrides or {})
    generate_keys = set(generate)

    if os.path.exists(dest_path) and not force:
        log.step(f"{dest_path} already present — leaving it untouched")
        return False
    if not os.path.exists(example_path):
        log.die(f"template not found: {example_path}")

    out_lines: list[str] = []
    seen: set[str] = set()
    with open(example_path, "r", encoding="utf-8") as handle:
        for line in handle:
            match = _ASSIGN.match(line)
            if not match:
                out_lines.append(line)
                continue
            indent, key, current = match.group(1), match.group(2), match.group(3)
            seen.add(key)
            value = _resolve_value(key, current, overrides, generate_keys)
            out_lines.append(f"{indent}{key}={value}\n")

    # Overrides for keys not present in the example are appended so nothing is lost.
    extra = [k for k in overrides if k not in seen]
    if extra:
        out_lines.append("\n# --- added by deploy (not in template) ---\n")
        out_lines.extend(f"{key}={overrides[key]}\n" for key in extra)

    _write_secure(dest_path, "".join(out_lines))
    log.ok(f"wrote {dest_path}")
    return True


def _resolve_value(
    key: str,
    current: str,
    overrides: Mapping[str, str],
    generate_keys: set[str],
) -> str:
    if key in overrides:
        return overrides[key]
    if key in generate_keys and current.strip() in _PLACEHOLDER_VALUES:
        return generate_secret()
    return current
