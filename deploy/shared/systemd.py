# vendored deploy library — do not edit here; regenerate from the deploy source.
"""Install and manage `systemctl --user` services.

Most services run as a user-level systemd service (no dedicated
account, no root): the process runs as the operator, and code/keys/.env live in
their home dir. This installs the unit, reloads, and enables it, then prints the
follow-ups (log tailing, and the one-time `enable-linger` that keeps the service
running across logout — which needs root, so it's a reminder rather than a step).
"""

from __future__ import annotations

import os
import shutil

import log
import proc

USER_UNIT_DIR = os.path.expanduser("~/.config/systemd/user")


def install_user_unit(unit_path: str, *, start: bool = True) -> None:
    """Install a `.service` file into the user unit dir and enable it."""
    if not os.path.isfile(unit_path):
        log.die(f"unit file not found: {unit_path}")
    name = os.path.basename(unit_path)
    os.makedirs(USER_UNIT_DIR, exist_ok=True)
    shutil.copy2(unit_path, os.path.join(USER_UNIT_DIR, name))
    log.step(f"installed {name} -> {USER_UNIT_DIR}")

    proc.run(["systemctl", "--user", "daemon-reload"])
    if start:
        proc.run(["systemctl", "--user", "enable", "--now", name])
        log.ok(f"started user service {name}")
    else:
        proc.run(["systemctl", "--user", "enable", name])
        log.ok(f"enabled user service {name} (not started)")

    unit = name[:-8] if name.endswith(".service") else name
    log.step(f"logs:    journalctl --user -u {unit} -f")
    user = os.environ.get("USER", "$USER")
    log.step(f"persist: sudo loginctl enable-linger {user}   (keeps it up across logout)")
