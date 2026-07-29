#!/usr/bin/env python3
"""Create the BD admin user and register the ds1 data service. Idempotent.

Usage (called by install.py, not normally run directly):
    uv run python3 deploy/bootstrap_bare.py <mongo_user> <mongo_pwd>

Connects to MongoDB on 127.0.0.1:27017 (the loopback-published container).
"""

from __future__ import annotations

import random
import string
import sys

from pymongo import MongoClient
from werkzeug.security import generate_password_hash


def main() -> None:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <mongo_user> <mongo_pwd>", file=sys.stderr)
        raise SystemExit(1)

    mongo_user, mongo_pwd = sys.argv[1], sys.argv[2]
    tmp_password = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(16))

    client: MongoClient = MongoClient(
        host="127.0.0.1", port=27017,
        username=mongo_user, password=mongo_pwd, authSource="admin",
    )
    db = client.buildingdepot

    try:
        db.user.insert_one({
            "email": "admin@buildingdepot.org",
            "password": generate_password_hash(tmp_password),
            "first_name": "Admin",
            "first_login": True,
            "role": "super",
        })
        print(f"\nadmin@buildingdepot.org / {tmp_password}  (change on first login)\n")
    except Exception as exc:
        if "duplicate key" in str(exc).lower():
            print("admin user already exists — skipping")
        else:
            raise

    # `host` is what CentralService uses to reach the replica's XML-RPC on :8080
    # (see CentralService/app/rpc/defs.py:get_remote). Bare-metal: localhost.
    # `port` is the replica's XML-RPC port (8080), NOT the DataService port (8082).
    db.data_service.update_one(
        {"name": "ds1"},
        {"$set": {
            "name": "ds1", "description": "", "host": "127.0.0.1", "port": "8080",
        }, "$setOnInsert": {"buildings": [], "admins": []}},
        upsert=True,
    )
    print("registered data service ds1 (host='127.0.0.1', port='8080')")


if __name__ == "__main__":
    main()
