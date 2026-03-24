#!/usr/bin/env bash
# Copy env.sample to .env and fill credential fields with random secrets (openssl).
# Safe for docker compose and local use; hex-only values avoid .env / shell quoting issues.

set -euo pipefail

SAMPLE="${SAMPLE:-env.sample}"
OUT="${OUT:-.env}"

usage() {
  cat <<EOF
Usage: $0 [-f|--force] [-h|--help]

  -f, --force   Overwrite existing .env without asking
  -h, --help    Show this help

Environment:
  SAMPLE   Path to sample file (default: env.sample)
  OUT      Output path (default: .env)
EOF
}

force=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    -f | --force) force=1 ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

if [[ ! -f "$SAMPLE" ]]; then
  echo "Sample file not found: $SAMPLE" >&2
  exit 1
fi

if [[ -f "$OUT" ]]; then
  if [[ "$force" -eq 1 ]]; then
    :
  else
    read -r -p ".env already exists. Overwrite? [y/N] " ans || true
    case "${ans:-}" in
      y | Y | yes | YES) ;;
      *)
        echo "Aborted." >&2
        exit 1
        ;;
    esac
  fi
fi

cp "$SAMPLE" "$OUT"

MONGO_ROOT_PASSWORD="$(openssl rand -hex 24)"
MONGODB_PWD="$(openssl rand -hex 24)"
REDIS_PWD="$(openssl rand -hex 32)"
INFLUXDB_PWD="$(openssl rand -hex 24)"
RABBITMQ_ADMIN_PWD="$(openssl rand -hex 24)"
SECRET_KEY="$(openssl rand -hex 32)"

sed -i \
  -e "s|^MONGO_ROOT_PASSWORD=.*|MONGO_ROOT_PASSWORD=$MONGO_ROOT_PASSWORD|" \
  -e "s|^MONGODB_PWD=.*|MONGODB_PWD=$MONGODB_PWD|" \
  -e "s|^REDIS_PWD=.*|REDIS_PWD=$REDIS_PWD|" \
  -e "s|^INFLUXDB_PWD=.*|INFLUXDB_PWD=$INFLUXDB_PWD|" \
  -e "s|^RABBITMQ_ADMIN_PWD=.*|RABBITMQ_ADMIN_PWD=$RABBITMQ_ADMIN_PWD|" \
  -e "s|^SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" \
  "$OUT"

echo "Wrote $OUT (passwords and SECRET_KEY randomized)."
