# vendored deploy library — do not edit here; regenerate from the deploy source.
"""Tiny `{{ KEY }}` templating with raise-on-missing-key.

Deliberately uses `{{ KEY }}` rather than `$KEY`/`${KEY}` so nginx's own
`$host`, `$remote_addr`, `$connection_upgrade`, … pass through untouched — the
renderer only ever rewrites our placeholders, never nginx (or shell) variables.

Keys are `[A-Za-z_][A-Za-z0-9_]*`. A placeholder with no matching key raises
`MissingKeyError`; that is intentional — a half-rendered config is worse than a
loud failure.
"""

from __future__ import annotations

import re
from typing import Mapping

_PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


class MissingKeyError(KeyError):
    """A `{{ KEY }}` placeholder had no corresponding value."""


def find_placeholders(text: str) -> set[str]:
    """Return the set of placeholder keys referenced in `text`."""
    return {match.group(1) for match in _PLACEHOLDER.finditer(text)}


def render(text: str, variables: Mapping[str, object]) -> str:
    """Substitute every `{{ KEY }}` in `text` from `variables`.

    Raises MissingKeyError if any placeholder has no value.
    """

    def _substitute(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in variables:
            raise MissingKeyError(
                f"no value for placeholder {{{{ {key} }}}} "
                f"(have: {', '.join(sorted(variables)) or 'none'})"
            )
        return str(variables[key])

    return _PLACEHOLDER.sub(_substitute, text)


def render_file(src_path: str, dest_path: str, variables: Mapping[str, object]) -> None:
    """Render `src_path` through `render()` and write the result to `dest_path`."""
    with open(src_path, "r", encoding="utf-8") as handle:
        rendered = render(handle.read(), variables)
    with open(dest_path, "w", encoding="utf-8") as handle:
        handle.write(rendered)
