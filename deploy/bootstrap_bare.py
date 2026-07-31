#!/usr/bin/env python3
"""Seed the records BD cannot start empty: admin user, ds1, OAuth client.

Usage (called by install.py, not normally run directly):
    uv run python3 deploy/bootstrap_bare.py --mongo-user U --mongo-pwd P \
        [--client-id ID --client-secret SECRET]

Connects to MongoDB on 127.0.0.1:27017 (the loopback-published container).
Every step is idempotent, so re-running after a config change is safe.
"""

from __future__ import annotations

import argparse
import random
import string

from pymongo import MongoClient
from pymongo.database import Database

ADMIN_EMAIL = "admin@buildingdepot.org"


def create_admin(db: Database) -> None:
    """Insert the super user, printing a one-time password. No-op if present."""
    from werkzeug.security import generate_password_hash

    tmp_password = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
    try:
        db.user.insert_one({
            "email": ADMIN_EMAIL,
            "password": generate_password_hash(tmp_password),
            "first_name": "Admin",
            "first_login": True,
            "role": "super",
        })
        print(f"\n{ADMIN_EMAIL} / {tmp_password}  (change on first login)\n")
    except Exception as exc:
        if "duplicate key" in str(exc).lower():
            print("admin user already exists — skipping")
        else:
            raise


def register_data_service(db: Database) -> None:
    """Register ds1 so CentralService can resolve the replica."""
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


def register_oauth_client(db: Database, client_id: str, client_secret: str) -> None:
    """Register a pre-declared OAuth client owned by the admin user.

    BD normally mints clients itself (`GET /oauth/client` returns a fresh
    id/secret pair), but a co-located MitesBackend needs the pair to exist
    *before* it first authenticates — the site manifest declares it and BD
    registers it here. BD's token endpoint only looks the pair up
    (`Client.objects(client_id=..., client_secret=...)` in
    `CentralService/app/oauth_bd/views.py:get_access_token`), so a declared pair
    is equivalent to a UI-minted one.

    The collection is `client`, mongoengine's default for the `Client` document.
    Addressed by subscript, not attribute: `Database.client` is a pymongo
    property that returns the MongoClient, so `db.client` would not be the
    collection.
    """
    db["client"].update_one(
        {"client_id": client_id},
        {"$set": {
            "client_id": client_id,
            "client_secret": client_secret,
            "user": ADMIN_EMAIL,
        }, "$setOnInsert": {
            # Matches what `GET /oauth/client` stores. The backend uses the
            # client-credentials path and never redirects, but the Client
            # document's `redirect_uris`/`default_scopes` properties split these
            # strings, so absent fields would break any authorization-code flow.
            "_redirect_uris": " ".join([
                "http://localhost:8000/authorized",
                "http://127.0.0.1:8000/authorized",
            ]),
            "_default_scopes": "email",
        }},
        upsert=True,
    )
    print(f"registered OAuth client '{client_id}' (owner: {ADMIN_EMAIL})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mongo-user", required=True, help="MongoDB admin username")
    parser.add_argument("--mongo-pwd", required=True, help="MongoDB admin password")
    parser.add_argument("--client-id", default="", help="pre-declared BD OAuth client id")
    parser.add_argument("--client-secret", default="", help="pre-declared BD OAuth client secret")
    args = parser.parse_args()

    connection: MongoClient = MongoClient(
        host="127.0.0.1", port=27017,
        username=args.mongo_user, password=args.mongo_pwd, authSource="admin",
    )
    db: Database = connection.buildingdepot

    create_admin(db)
    register_data_service(db)

    if args.client_id and args.client_secret:
        register_oauth_client(db, args.client_id, args.client_secret)
    else:
        print("no OAuth client declared — skipping (mint one via GET /oauth/client)")


if __name__ == "__main__":
    main()
