# vendored deploy library — do not edit here; regenerate from the deploy source.
"""Install and manage `systemctl --user` services.

Most services run as a user-level systemd service (no dedicated
account, no root): the process runs as the operator, and code/keys/.env live in
their home dir. This installs the unit, reloads, and enables it, then prints the
follow-ups (log tailing, and the one-time `enable-linger` that keeps the service
running across logout — which needs root, so it's a reminder rather than a step).

Unit files whose `WorkingDirectory` (and any absolute paths) depend on where the
repo was cloned ship as `<name>.service.template` with `{{ WORKING_DIRECTORY }}`
placeholders. The caller passes the repo root it computed as `variables`, so the
same template installs correctly regardless of clone location — no hand-editing
the installed unit.
"""

from __future__ import annotations

import os
import shutil
from typing import Mapping

import log
import proc
import template

USER_UNIT_DIR = os.path.expanduser("~/.config/systemd/user")

_TEMPLATE_SUFFIX = ".template"


def install_user_unit(
    unit_path: str,
    *,
    variables: Mapping[str, object] | None = None,
    start: bool = True,
) -> None:
    """Install a `.service` unit into the user unit dir and enable it.

    A `<name>.service.template` source is rendered through `template` (using
    `variables`) and installed as `<name>.service`; a plain `.service` source is
    copied verbatim. Pass `variables` whenever the unit has `{{ KEY }}`
    placeholders — a missing key raises rather than installing a broken unit.
    """
    if not os.path.isfile(unit_path):
        log.die(f"unit file not found: {unit_path}")
    src_name = os.path.basename(unit_path)
    dest_name = (
        src_name[: -len(_TEMPLATE_SUFFIX)]
        if src_name.endswith(_TEMPLATE_SUFFIX)
        else src_name
    )
    os.makedirs(USER_UNIT_DIR, exist_ok=True)
    dest_path = os.path.join(USER_UNIT_DIR, dest_name)
    if variables is not None:
        template.render_file(unit_path, dest_path, variables)
    else:
        shutil.copy2(unit_path, dest_path)
    log.step(f"installed {dest_name} -> {USER_UNIT_DIR}")

    proc.run(["systemctl", "--user", "daemon-reload"])
    if start:
        proc.run(["systemctl", "--user", "enable", "--now", dest_name])
        log.ok(f"started user service {dest_name}")
    else:
        proc.run(["systemctl", "--user", "enable", dest_name])
        log.ok(f"enabled user service {dest_name} (not started)")

    unit = dest_name[:-8] if dest_name.endswith(".service") else dest_name
    log.step(f"logs:    journalctl --user -u {unit} -f")
    user = os.environ.get("USER", "$USER")
    log.step(f"persist: sudo loginctl enable-linger {user}   (keeps it up across logout)")
