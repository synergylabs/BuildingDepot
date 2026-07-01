#!/usr/bin/env bash
# Render bd_settings.cfg + CentralReplica/config.py from env at container
# start, then exec the per-service command. Doing it here (not at build
# time) keeps secrets out of the image.
set -euo pipefail

: "${SECRET_KEY:?required}"
: "${MONGO_USER:?required}"
: "${MONGO_PWD:?required}"
: "${INFLUX_USER:?required}"
: "${INFLUX_PWD:?required}"
: "${INFLUX_DB:?required}"
: "${REDIS_PWD:?required}"
: "${RABBIT_ADMIN_USER:?required}"
: "${RABBIT_ADMIN_PWD:?required}"
: "${RABBIT_END_USER:?required}"
: "${RABBIT_END_PWD:?required}"

cat >"$BD_SETTINGS" <<EOF
DEBUG = False
SECRET_KEY = '$SECRET_KEY'
TOKEN_EXPIRATION = 3600
EMAIL = 'LOCAL'
EMAIL_ID = 'admin@buildingdepot.org'
SMTP_HOST = '${SMTP_HOST:-localhost}'
SMTP_PORT = ${SMTP_PORT:-25}
NOTIFICATION_TYPE = 'RabbitMQ'

MONGODB_HOST = 'mongo'
MONGODB_PORT = 27017
MONGODB_DATABASE = 'buildingdepot'
MONGODB_DATABASE_DS = 'dataservice'
MONGODB_DATABASE_BD = 'buildingdepot'
MONGODB_USERNAME = '$MONGO_USER'
MONGODB_PWD = '$MONGO_PWD'

REDIS_HOST = 'redis'
REDIS_PWD = '$REDIS_PWD'

NAME = 'ds1'

INFLUXDB_HOST = 'influxdb'
INFLUXDB_PORT = 8086
INFLUXDB_DB = '$INFLUX_DB'
INFLUXDB_USERNAME = '$INFLUX_USER'
INFLUXDB_PWD = '$INFLUX_PWD'

RABBITMQ_HOST = 'rabbitmq'
RABBITMQ_ADMIN_USERNAME = '$RABBIT_ADMIN_USER'
RABBITMQ_ADMIN_PWD = '$RABBIT_ADMIN_PWD'
RABBITMQ_ENDUSER_USERNAME = '$RABBIT_END_USER'
RABBITMQ_ENDUSER_PWD = '$RABBIT_END_PWD'
EOF

# CentralReplica imports plain `from config import Config` — no Flask
# settings file. Overwrite its module-level config.py from env.
cat >/app/buildingdepot/CentralReplica/config.py <<EOF
class Config:
    MONGODB_DATABASE = "buildingdepot"
    MONGODB_HOST = "mongo"
    MONGODB_PORT = 27017
    SECRET_KEY = "$SECRET_KEY"
    TOKEN_EXPIRATION = 3600
    REDIS_HOST = "redis"
    MONGODB_USERNAME = "$MONGO_USER"
    MONGODB_PWD = "$MONGO_PWD"
    REDIS_PWD = "$REDIS_PWD"
EOF

# Legacy CS + DS hardcode the CentralReplica's XML-RPC client to localhost.
# In our compose stack the replica is its own container — patch the URL.
sed -i 's|ServerProxy("http://127.0.0.1:8080")|ServerProxy("http://bd-replica:8080")|' \
    /app/buildingdepot/DataService/app/__init__.py
sed -i 's|ServerProxy("http://localhost:8080")|ServerProxy("http://bd-replica:8080")|' \
    /app/buildingdepot/CentralService/app/__init__.py

exec "$@"
