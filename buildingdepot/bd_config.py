"""
buildingdepot.bd_config
~~~~~~~~~~~~~~~~~~~~~~~

The single source of BuildingDepot runtime configuration.

All three services (CentralService, DataService, CentralReplica) read their
settings from here, and everything site-specific comes from one file: `.env` at
the repo root. There is no generated `bd_settings.cfg` and no generated
`CentralReplica/config.py` — a value is either a secret/endpoint in `.env` or a
structural constant defined below.

Resolution order for a key, highest priority first:

  1. the process environment (so systemd or CI can override without editing a file)
  2. `.env` (path overridable with `BD_ENV`, default `<repo root>/.env`)
  3. the default assigned below; keys with no default are required and raise at
     import time rather than failing later inside a database driver

`.env` keys are the Flask config keys verbatim, so there is no name mapping to
keep in sync.

@copyright: (c) 2024 SynergyLabs
@license: CMU License. See License file for details.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Final

REPO_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
DEFAULT_ENV_PATH: Final[Path] = REPO_ROOT / ".env"

# KEY=VALUE, tolerating leading whitespace and an optional `export `.
_ASSIGN: Final[re.Pattern[str]] = re.compile(
    r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$"
)

# Values that mean "the operator has not filled this in yet". Treated as absent
# so a half-provisioned .env fails loudly instead of connecting with "replace-me".
_PLACEHOLDERS: Final[frozenset[str]] = frozenset(
    {"", "replace-me", "replace-me-with-openssl-rand-hex-32"}
)

_TRUTHY: Final[frozenset[str]] = frozenset({"1", "true", "yes", "on"})

# Optional keys with no default: absent from the config dict entirely, because
# CentralService probes them with try/except KeyError (Firebase notifications)
# or only touches them on the GMAIL mail path.
_OPTIONAL_KEYS: Final[tuple[str, ...]] = (
    "FIREBASE_CREDENTIALS",
    "CLIENT_ID",
    "CLIENT_SECRET",
    "REFRESH_TOKEN",
)


def _parse_env_file(path: Path) -> dict[str, str]:
    """Parse a `.env` file into a dict. Comments and blank lines are skipped.

    Surrounding single/double quotes on values are stripped. Missing file -> {}.
    """
    values: dict[str, str] = {}
    if not path.exists():
        return values
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            match = _ASSIGN.match(line)
            if match is None:
                continue
            raw = match.group(2).strip()
            if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ("'", '"'):
                raw = raw[1:-1]
            values[match.group(1)] = raw
    return values


def _load() -> dict[str, str]:
    env_path = Path(os.environ.get("BD_ENV") or DEFAULT_ENV_PATH)
    values = _parse_env_file(env_path)
    # A blank process variable must not mask a good value from the file.
    values.update({k: v for k, v in os.environ.items() if v.strip()})
    return values


_VALUES: Final[dict[str, str]] = _load()


def _required(key: str) -> str:
    value = _VALUES.get(key, "").strip()
    if value in _PLACEHOLDERS:
        raise RuntimeError(
            f"{key} is missing or still a placeholder. Set it in "
            f"{os.environ.get('BD_ENV') or DEFAULT_ENV_PATH} "
            f"(run `python3 deploy/install.py` to provision one)."
        )
    return value


def _text(key: str, default: str) -> str:
    value = _VALUES.get(key, "").strip()
    return value if value not in _PLACEHOLDERS else default


def _number(key: str, default: int) -> int:
    value = _VALUES.get(key, "").strip()
    if value in _PLACEHOLDERS:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{key} must be an integer, got {value!r}") from exc


def _flag(key: str, default: bool) -> bool:
    value = _VALUES.get(key, "").strip()
    return value.lower() in _TRUTHY if value not in _PLACEHOLDERS else default


class Config:
    """Every BD setting, resolved. CentralReplica reads these attributes
    directly; CentralService and DataService load `CONFIG` into `app.config`."""

    # --- Flask ---
    DEBUG: bool = _flag("DEBUG", False)
    SECRET_KEY: str = _required("SECRET_KEY")
    TOKEN_EXPIRATION: int = _number("TOKEN_EXPIRATION", 3600)

    # --- Mail ---
    EMAIL: str = _text("EMAIL", "LOCAL")
    EMAIL_ID: str = _text("EMAIL_ID", "admin@buildingdepot.org")
    SMTP_HOST: str = _text("SMTP_HOST", "localhost")
    SMTP_PORT: int = _number("SMTP_PORT", 25)

    # --- Notifications ---
    NOTIFICATION_TYPE: str = _text("NOTIFICATION_TYPE", "RabbitMQ")

    # --- MongoDB (loopback container) ---
    MONGODB_HOST: str = _text("MONGODB_HOST", "127.0.0.1")
    MONGODB_PORT: int = _number("MONGODB_PORT", 27017)
    MONGODB_USERNAME: str = _text("MONGODB_USERNAME", "bdadmin")
    MONGODB_PWD: str = _required("MONGODB_PWD")
    # Database names are structural, not per-site.
    MONGODB_DATABASE: str = "buildingdepot"
    MONGODB_DATABASE_BD: str = "buildingdepot"
    MONGODB_DATABASE_DS: str = "dataservice"

    # --- Redis / Valkey (bare metal) ---
    REDIS_HOST: str = _text("REDIS_HOST", "127.0.0.1")
    REDIS_PWD: str = _required("REDIS_PWD")

    # --- InfluxDB 1.x (loopback container) ---
    INFLUXDB_HOST: str = _text("INFLUXDB_HOST", "127.0.0.1")
    INFLUXDB_PORT: int = _number("INFLUXDB_PORT", 8086)
    INFLUXDB_DB: str = _text("INFLUXDB_DB", "buildingdepot")
    INFLUXDB_USERNAME: str = _text("INFLUXDB_USERNAME", "bdadmin")
    INFLUXDB_PWD: str = _required("INFLUXDB_PWD")

    # --- RabbitMQ (bare metal) ---
    RABBITMQ_HOST: str = _text("RABBITMQ_HOST", "127.0.0.1")
    RABBITMQ_ADMIN_USERNAME: str = _text("RABBITMQ_ADMIN_USERNAME", "bdadmin")
    RABBITMQ_ADMIN_PWD: str = _required("RABBITMQ_ADMIN_PWD")
    RABBITMQ_ENDUSER_USERNAME: str = _text("RABBITMQ_ENDUSER_USERNAME", "bduser")
    RABBITMQ_ENDUSER_PWD: str = _required("RABBITMQ_ENDUSER_PWD")

    # --- This DataService's registered name ---
    NAME: str = "ds1"


def _build_config() -> dict[str, object]:
    config: dict[str, object] = {
        key: value for key, value in vars(Config).items() if key.isupper()
    }
    for key in _OPTIONAL_KEYS:
        value = _VALUES.get(key, "").strip()
        if value not in _PLACEHOLDERS:
            config[key] = value
    return config


#: Ready to hand to `app.config.update(...)`.
CONFIG: Final[dict[str, object]] = _build_config()
