# vendored deploy library — do not edit here; regenerate from the deploy source.
"""The site manifest: one source of truth for cross-component wiring.

A host running several services keeps a single `site.env` holding the shared
endpoints (BD host/ports, RabbitMQ, backend URL) and the secrets generated once
and consumed by more than one app (the BD OAuth client, the RabbitMQ end-user).
Each app's `install.py` declares a *mapping* from manifest keys to its own
`.env` keys and calls `apply_site_env`; the manifest then fills that app's
`.env` placeholders.

The manifest is optional. With none present, `apply_site_env` falls back to the
app's standalone `.env.example` flow — which is what keeps an app (notably
BuildingDepot) deployable on its own with no dependency on this tooling.

Resolution order for the manifest path:
  1. an explicit path passed by the caller (if it exists)
  2. the `SITE_ENV` environment variable (if set and the file exists)
  3. none -> standalone fallback

`SITE_ENV` is deliberately a neutral name: nothing in this vendored payload
refers to any specific project.
"""

from __future__ import annotations

import os
import string
from typing import Callable, Mapping, Union

import env as env_module
import log

# A mapping value is either a manifest key (copied verbatim) or a callable that
# derives the value from the whole manifest (e.g. building a URL from host+port).
MappingValue = Union[str, Callable[[Mapping[str, str]], "str | None"]]


def derive(fmt: str) -> Callable[[Mapping[str, str]], "str | None"]:
    """Build a mapping callable that fills `fmt` from the manifest.

    `fmt` is a `str.format`-style template over manifest keys, e.g.
    `"{BD_SCHEME}://{BD_HOST}:{BD_CS_PORT}"`. The callable returns None if any
    referenced key is missing or blank, so an incomplete manifest leaves the
    app's own default in place instead of producing a malformed value.
    """
    keys = [name for _, name, _, _ in string.Formatter().parse(fmt) if name]

    def _fill(site: Mapping[str, str]) -> "str | None":
        if any(not site.get(key) for key in keys):
            return None
        return fmt.format(**{key: site[key] for key in keys})

    return _fill


def find_site_env(explicit_path: str | None = None) -> str | None:
    """Return the manifest path to use, or None if there is no manifest."""
    if explicit_path and os.path.exists(explicit_path):
        return explicit_path
    from_env = os.environ.get("SITE_ENV")
    if from_env and os.path.exists(from_env):
        return from_env
    return None


def load_site_env(explicit_path: str | None = None) -> dict[str, str]:
    """Load the manifest into a dict, or return {} when none is present."""
    path = find_site_env(explicit_path)
    if path is None:
        return {}
    log.step(f"using site manifest: {path}")
    return env_module.read_env(path)


def resolve_overrides(
    site: Mapping[str, str],
    mapping: Mapping[str, MappingValue],
) -> dict[str, str]:
    """Turn (manifest, mapping) into concrete `.env` overrides.

    Keys whose source is missing from the manifest (or whose callable returns
    None) are omitted, so the app's own `.env.example` default survives.
    """
    overrides: dict[str, str] = {}
    for app_key, source in mapping.items():
        if callable(source):
            value = source(site)
        else:
            value = site.get(source)
        if value is not None and value != "":
            overrides[app_key] = value
    return overrides


def apply_site_env(
    example_path: str,
    dest_path: str,
    mapping: Mapping[str, MappingValue],
    *,
    generate: tuple[str, ...] = (),
    site_path: str | None = None,
    force: bool = False,
) -> bool:
    """Provision an app `.env` from its example plus the site manifest.

    With a manifest present, mapped keys override the example's defaults; without
    one, only `generate` keys and the example defaults apply. Returns whether a
    file was written (see `env.provision_env`).
    """
    site = load_site_env(site_path)
    overrides = resolve_overrides(site, mapping)
    return env_module.provision_env(
        example_path,
        dest_path,
        overrides=overrides,
        generate=generate,
        force=force,
    )
