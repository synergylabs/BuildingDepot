#!/usr/bin/env bash
# One-shot: create the BD admin user inside the running bd-central container.
# Idempotent: if the user already exists, MongoDB raises DuplicateKey and we exit 0.
set -euo pipefail

cd "$(dirname "$0")"

if ! docker compose ps --status running bd-central | grep -q bd-central ; then
  echo "bd-central not running — start the stack first: docker compose up -d" >&2
  exit 1
fi

docker compose exec -T bd-central python3 - <<'PY'
import configparser, io, os, random, string
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

cfg = configparser.ConfigParser()
buf = io.StringIO('[s]\n' + open(os.environ['BD_SETTINGS']).read())
cfg.read_file(buf)
user = cfg.get('s', 'MONGODB_USERNAME').strip("'\"")
pwd  = cfg.get('s', 'MONGODB_PWD').strip("'\"")

tmp = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
client = MongoClient(host='mongo', port=27017, username=user, password=pwd, authSource='admin')
db = client.buildingdepot
try:
    db.user.insert_one({
        'email': 'admin@buildingdepot.org',
        'password': generate_password_hash(tmp),
        'first_name': 'Admin',
        'first_login': True,
        'role': 'super',
    })
    print(f'\nadmin@buildingdepot.org / {tmp}  (change on first login)\n')
except Exception as e:
    if 'duplicate key' in str(e).lower():
        print('admin user already exists — skipping')
    else:
        raise

# `host` is what CentralService uses to call the replica's XML-RPC on :8080
# (see CentralService/app/rpc/defs.py:get_remote). Must point at the replica
# container, NOT bd-data — they are separate services in the compose stack.
db.data_service.update_one(
    {'name': 'ds1'},
    {'$set': {
        'name': 'ds1', 'description': '', 'host': 'bd-replica', 'port': 8082,
    }, '$setOnInsert': {'buildings': [], 'admins': []}},
    upsert=True,
)
print("registered data service ds1 (host='bd-replica' for XML-RPC)")
PY
