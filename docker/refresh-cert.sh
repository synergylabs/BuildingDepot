#!/usr/bin/env bash
# Provision/renew the TLS cert nginx serves on CS:81 / DS:82, then reload nginx.
#
# nginx only ever reads certs/bd.crt + certs/bd.key. This script fills those two
# files from one of two issuers, picked by CERT_PROVIDER:
#
#   certbot    -- PUBLIC IP + real domain. Let's Encrypt via certbot (HTTP-01 on
#                 :80). Needs the domain's A record -> this host and port 80 free.
#                 certbot installs its own renewal timer; point its --deploy-hook
#                 at this script so renewals recopy the PEMs and reload nginx.
#
#   tailscale  -- PRIVATE / no public IP (default). Cert from Tailscale for the
#                 node's MagicDNS name, Let's Encrypt backed, validated over the
#                 ts.net DNS. Re-run on a daily timer to renew.
#
# Usage:
#   sudo ./refresh-cert.sh                                                  # tailscale, auto domain
#   sudo BD_CERT_DOMAIN=bd.example.com CERT_PROVIDER=certbot ./refresh-cert.sh
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
CERT_DIR="$DIR/certs"
PROVIDER="${CERT_PROVIDER:-tailscale}"
mkdir -p "$CERT_DIR"

# Fingerprint the current cert so we only bounce services on a real renewal.
OLD_HASH="$([ -f "$CERT_DIR/bd.crt" ] && sha256sum "$CERT_DIR/bd.crt" | cut -d' ' -f1 || echo none)"

case "$PROVIDER" in
  certbot)
    : "${BD_CERT_DOMAIN:?set BD_CERT_DOMAIN to your public domain}"
    echo "[certbot] obtaining/renewing Let's Encrypt cert for $BD_CERT_DOMAIN"
    args=(certonly --standalone --non-interactive --agree-tos -d "$BD_CERT_DOMAIN")
    if [ -n "${CERTBOT_EMAIL:-}" ]; then args+=(-m "$CERTBOT_EMAIL"); else args+=(--register-unsafely-without-email); fi
    certbot "${args[@]}"
    LE="/etc/letsencrypt/live/$BD_CERT_DOMAIN"
    cp "$LE/fullchain.pem" "$CERT_DIR/bd.crt"
    cp "$LE/privkey.pem"   "$CERT_DIR/bd.key"
    ;;

  tailscale)
    DOMAIN="${BD_CERT_DOMAIN:-$(tailscale status --json | python3 -c 'import sys,json; print(json.load(sys.stdin)["CertDomains"][0])')}"
    echo "[tailscale] issuing/renewing cert for $DOMAIN"
    tailscale cert --cert-file "$CERT_DIR/bd.crt" --key-file "$CERT_DIR/bd.key" "$DOMAIN"
    ;;

  *)
    echo "unknown CERT_PROVIDER: $PROVIDER (use certbot|tailscale)" >&2
    exit 1
    ;;
esac

# Only nginx reads these (it terminates TLS for CS/DS on 81/82 and for RabbitMQ
# web-STOMP wss on 15675), and its container process runs as root, so owner-only
# on the key is enough under both rootful Docker and rootless Podman. The cert is
# public; the key stays 0600.
chmod 0644 "$CERT_DIR/bd.crt"
chmod 0600 "$CERT_DIR/bd.key"

# Only reload if the cert actually changed, so a daily timer is a no-op until a
# real renewal and does not bounce the broker every day.
NEW_HASH="$(sha256sum "$CERT_DIR/bd.crt" | cut -d' ' -f1)"
if [ "$NEW_HASH" = "$OLD_HASH" ]; then
  echo "cert unchanged, nothing to reload."
  exit 0
fi

# setup.sh issues the cert before the stack exists and brings nginx up itself,
# so it calls this with RELOAD_NGINX=0 to get just the PEMs. Default stays 1 so
# a renewal timer reloads exactly as before.
if [ "${RELOAD_NGINX:-1}" != "1" ]; then
  echo "cert written; skipping nginx reload (RELOAD_NGINX=$RELOAD_NGINX)."
  exit 0
fi

# nginx terminates all TLS (CS/DS on 81/82 and web-STOMP wss on 15675), so a
# renewal only needs nginx to reload. It reloads in place; fall back to a recreate
# if it is not up yet.
if docker compose -f "$DIR/docker-compose.yml" exec -T nginx nginx -s reload 2>/dev/null; then
  echo "nginx reloaded."
else
  docker compose -f "$DIR/docker-compose.yml" up -d --force-recreate nginx
  echo "nginx (re)started."
fi
