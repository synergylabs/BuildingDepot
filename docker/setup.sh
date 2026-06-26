#!/usr/bin/env bash
#
# Guided one-shot setup for the BuildingDepot docker stack on a fresh host.
#
# Walks the three things you otherwise do by hand (docker/README.md "Quick
# start"): fill docker/.env with real secrets, provision the TLS cert nginx
# serves, bring the stack up, and create the admin user. Re-runnable: it fills
# only what is missing and never clobbers values you already set.
#
#   ./setup.sh
#
# It does NOT install packages. On a vanilla box, install docker + openssl (and,
# for the cert step, tailscale or certbot) first; the script checks for each and
# tells you exactly what is missing.
#
# What it deliberately does NOT touch, so a co-located service is safe:
#   - The stack publishes 81/82/15675 (+5672/15672/15674/8025), never 80 or 443.
#     If MitesBackend3.0 (or any reverse proxy) already owns 80/443 on this host,
#     the two coexist. The only clash is certbot --standalone wanting port 80 —
#     the script detects that and steers you to Tailscale or an existing cert.
#   - nginx.conf is the security boundary (TLS for CS/DS/RMQ, the 497 redirect).
#     This script renders no nginx config and adds no host-level redirect.
#
set -euo pipefail

cd "$(dirname "$0")"                       # always operate from docker/
DIR="$(pwd)"
CERT_DIR="$DIR/certs"

# Host ports the stack publishes (compose reads these from .env; defaults match
# docker-compose.yml). Mailpit's 8025 is hardcoded in compose, listed for the
# conflict scan only.
declare -A PORTS=(
  [CS]=81 [DS]=82 [RABBIT_WSS]=15675
  [AMQP]=5672 [RABBIT_MGMT]=15672 [RABBIT_WS]=15674
)

# --- tiny ui helpers (same idiom as MitesBackend3.0/deploy/setup-proxy.sh) -----
have()    { command -v "$1" >/dev/null 2>&1; }
say()     { printf '%s\n' "$*"; }
warn()    { printf 'warning: %s\n' "$*" >&2; }
die()     { printf 'error: %s\n' "$*" >&2; exit 1; }
ask()     { local p="$1" d="${2:-}" a; read -r -p "$p" a </dev/tty || true; printf '%s' "${a:-$d}"; }
confirm() { local a; a="$(ask "$1 [y/N]: ")"; [[ "$a" == [yY] || "$a" == [yY][eE][sS] ]]; }

# Detect-only; never installs. Dies with an actionable message if absent.
need() { have "$1" || die "$1 not found — install it and re-run. ($2)"; }

# docker compose v2 (`docker compose`) preferred, v1 (`docker-compose`) fallback.
DC=""
pick_compose() {
  if docker compose version >/dev/null 2>&1; then DC="docker compose"
  elif have docker-compose;              then DC="docker-compose"
  else die "docker compose not found — install the Compose plugin and re-run."; fi
}

# sudo prefix for the privileged cert tooling only (tailscale/certbot need root).
# Everything else — compose, openssl, file writes — runs as the invoking user so
# a rootless docker/podman setup keeps working.
SUDO=""
[[ $EUID -ne 0 ]] && have sudo && SUDO="sudo"

# True if the docker engine is rootless (podman or rootless dockerd). Affects
# cert file ownership and privileged-port advice.
is_rootless() {
  docker info 2>/dev/null | grep -qiE 'rootless|podman'
}

# True if this compose project already has containers (running or stopped) — i.e.
# this is a re-run / post-crash run, not a fresh host. Used to skip the fresh-host
# port-conflict scan so the stack's own published ports aren't flagged as clashes.
stack_running() { [[ -n "$($DC ps -q 2>/dev/null)" ]]; }

# Is a TCP port already being listened on locally?
port_in_use() {
  local p="$1"
  if have ss;   then ss -ltnH "( sport = :$p )" 2>/dev/null | grep -q .; return; fi
  if have lsof; then lsof -iTCP:"$p" -sTCP:LISTEN >/dev/null 2>&1; return; fi
  (exec 3<>"/dev/tcp/127.0.0.1/$p") 2>/dev/null && return 0 || return 1
}

# Best-effort "what is this process" for a listening port.
who_on_port() {
  local p="$1"
  if have ss; then ss -ltnpH "( sport = :$p )" 2>/dev/null \
      | grep -oE 'users:\(\("[^"]+"' | head -1 | sed -E 's/.*\("//'; fi
}

# ------------------------------------------------------------------------------
# 1. .env — create from the example and fill secrets, without clobbering values.
# ------------------------------------------------------------------------------
SECRET_VARS=(SECRET_KEY MONGO_PWD INFLUX_PWD REDIS_PWD RABBIT_ADMIN_PWD RABBIT_END_PWD)

gen_secret() { openssl rand -hex 32; }

# Replace KEY=... only when the current value is still a placeholder
# (empty or matches replace-me*). Real values are left untouched.
fill_if_placeholder() {
  local key="$1" val="$2" cur
  cur="$(grep -E "^${key}=" .env | head -1 | cut -d= -f2-)"
  if [[ -z "$cur" || "$cur" == replace-me* ]]; then
    # portable in-place edit (BSD/GNU sed differ on -i); use a temp file
    sed -E "s|^${key}=.*|${key}=${val}|" .env > .env.tmp && mv .env.tmp .env
    return 0
  fi
  return 1
}

ensure_env() {
  say "== Step 1/4: docker/.env =="
  if [[ ! -f .env ]]; then
    [[ -f .env.example ]] || die "missing .env.example — are you in the docker/ dir of the repo?"
    cp .env.example .env
    say "created .env from .env.example"
  else
    say ".env already exists — filling only placeholders, keeping your values"
  fi

  local filled=0
  for v in "${SECRET_VARS[@]}"; do
    if fill_if_placeholder "$v" "$(gen_secret)"; then filled=$((filled+1)); fi
  done
  say "secrets: ${filled} generated, $(( ${#SECRET_VARS[@]} - filled )) already set"

  # Fail loudly if any placeholder survives (entrypoint.sh would otherwise abort
  # deep inside the container with a less obvious :?required error).
  if grep -qE '=replace-me' .env; then
    grep -nE '=replace-me' .env >&2
    die "the lines above still say replace-me — edit them, then re-run."
  fi
  say
}

# ------------------------------------------------------------------------------
# 2. Ports — surface conflicts and the co-deploy picture before bringing up.
# ------------------------------------------------------------------------------
# Read a single var from .env (used to honour any HOST_PORT_* the user set).
env_val() { grep -E "^$1=" .env 2>/dev/null | head -1 | cut -d= -f2-; }

choose_ports() {
  say "== Step 2/4: ports =="

  # Co-deploy awareness: BD never uses 80/443, but a proxy that does (e.g. a
  # host nginx fronting MitesBackend) changes which cert path is safe.
  local p80 p443
  port_in_use 80  && p80="$(who_on_port 80)"
  port_in_use 443 && p443="$(who_on_port 443)"
  if [[ -n "${p80:-}${p443:-}" ]]; then
    say "note: something already listens on${p80:+ 80 ($p80)}${p443:+ 443 ($p443)}."
    say "      That's fine — this stack uses 81/82/15675 and never binds 80/443,"
    say "      so it coexists with a reverse proxy already on this host."
    CODEPLOY=1
  fi

  # Honour HOST_PORT_CS / HOST_PORT_DS from .env if present, else the defaults.
  PORTS[CS]="$(env_val HOST_PORT_CS)";        PORTS[CS]="${PORTS[CS]:-81}"
  PORTS[DS]="$(env_val HOST_PORT_DS)";        PORTS[DS]="${PORTS[DS]:-82}"
  PORTS[RABBIT_WSS]="$(env_val HOST_PORT_RABBIT_WSS)"; PORTS[RABBIT_WSS]="${PORTS[RABBIT_WSS]:-15675}"

  # Privileged-port heads-up under rootless engines (81/82 are <1024). Only on a
  # fresh setup — never offer to move ports out from under a running stack.
  if ! stack_running && is_rootless && { (( PORTS[CS] < 1024 )) || (( PORTS[DS] < 1024 )); }; then
    say "note: rootless engine + privileged ports (${PORTS[CS]}/${PORTS[DS]})."
    if confirm "Remap CS/DS to 8081/8082 in .env to avoid needing a sysctl change?"; then
      _set_env HOST_PORT_CS 8081; PORTS[CS]=8081
      _set_env HOST_PORT_DS 8082; PORTS[DS]=8082
      say "set HOST_PORT_CS=8081, HOST_PORT_DS=8082"
    else
      say "keeping ${PORTS[CS]}/${PORTS[DS]} — needs: sudo sysctl -w net.ipv4.ip_unprivileged_port_start=80"
    fi
  fi

  # Flag any publish port already taken (a hard 'compose up' failure otherwise).
  # Skip on a re-run: once our own project exists, its ports are expected and
  # 'compose up' just reconciles — scanning them would false-flag BD against
  # itself. The scan is a fresh-host courtesy, not a gate.
  if stack_running; then
    say "stack already present — reusing its published ports (re-run is safe)."
  else
    local clash=0 name port
    for name in "${!PORTS[@]}"; do
      port="${PORTS[$name]}"
      if port_in_use "$port"; then
        warn "host port $port ($name) is already in use by '$(who_on_port "$port")'."
        clash=1
      fi
    done
    if (( clash )); then
      say "Resolve by stopping the other listener or remapping via HOST_PORT_* in .env"
      say "(see docker/README.md 'Public ports'). Re-run when clear."
      confirm "Continue anyway?" || die "aborted on port conflict"
    fi
  fi
  say
}

# Set/replace a KEY=VALUE in .env (used for the port remap above).
_set_env() {
  local k="$1" v="$2"
  if grep -qE "^${k}=" .env; then
    sed -E "s|^${k}=.*|${k}=${v}|" .env > .env.tmp && mv .env.tmp .env
  else
    printf '%s=%s\n' "$k" "$v" >> .env
  fi
}

# ------------------------------------------------------------------------------
# 3. TLS cert — nginx serves one cert for CS(81)/DS(82)/RMQ-wss(15675).
#    refresh-cert.sh is the issuing primitive; we drive it, keep it as the thing
#    a renewal timer also runs. RELOAD_NGINX=0 because nginx isn't up yet here.
# ------------------------------------------------------------------------------
REACH_HOST="localhost"   # for the closing summary; refined per cert path

cert_is_valid() {
  [[ -f "$CERT_DIR/bd.crt" && -f "$CERT_DIR/bd.key" ]] || return 1
  openssl x509 -checkend 0 -noout -in "$CERT_DIR/bd.crt" >/dev/null 2>&1
}

# After privileged issuance the PEMs may be root-owned; a rootless container
# can't read a 0600 root key. Hand them to the user who runs compose.
fix_cert_ownership() {
  if is_rootless && [[ -n "$SUDO" ]]; then
    $SUDO chown "$(id -un):$(id -gn)" "$CERT_DIR/bd.crt" "$CERT_DIR/bd.key" 2>/dev/null || true
  fi
}

cert_tailscale() {
  need tailscale "https://tailscale.com/install.sh, then 'sudo tailscale up' + enable HTTPS certs"
  REACH_HOST="$(tailscale status --json 2>/dev/null \
      | grep -oE '"DNSName":[[:space:]]*"[^"]+"' | head -1 | sed -E 's/.*"([^"]+)"/\1/; s/\.$//')"
  say "issuing a Tailscale (Let's Encrypt) cert${REACH_HOST:+ for $REACH_HOST} ..."
  $SUDO env RELOAD_NGINX=0 CERT_PROVIDER=tailscale ./refresh-cert.sh
  fix_cert_ownership
}

cert_certbot() {
  need certbot "apt install certbot — needs port 80 free and a public DNS A record"
  if port_in_use 80; then
    warn "port 80 is in use by '$(who_on_port 80)'. certbot --standalone needs it free."
    say  "On a co-deployed host (e.g. a backend nginx on 80/443), prefer Tailscale or"
    say  "option 3 (reuse a cert that host already holds). Free port 80 to use certbot."
    confirm "Try certbot anyway?" || die "aborted certbot on port-80 conflict"
  fi
  local domain email
  domain="$(ask 'Public DNS name (A record -> this host): ')"; [[ -n "$domain" ]] || die "domain required"
  email="$(ask 'Contact email for renewal notices: ')";        [[ -n "$email" ]]  || die "email required"
  REACH_HOST="$domain"
  $SUDO env RELOAD_NGINX=0 CERT_PROVIDER=certbot BD_CERT_DOMAIN="$domain" CERTBOT_EMAIL="$email" ./refresh-cert.sh
  fix_cert_ownership
}

# Reuse a cert+key you already hold — e.g. the one MitesBackend already
# provisioned for this same host. Copied (not symlinked) so the bind mount
# resolves inside the container.
cert_existing() {
  local crt key sn
  sn="$(ask 'Server name this cert is for (for the summary URL): ' "$(hostname -f 2>/dev/null || hostname)")"
  crt="$(ask 'Path to fullchain/cert .pem: ')"; [[ -f "$crt" ]] || die "cert not found: $crt"
  key="$(ask 'Path to private key .pem: ')";   [[ -f "$key" ]] || die "key not found: $key"
  mkdir -p "$CERT_DIR"
  $SUDO cp "$crt" "$CERT_DIR/bd.crt"
  $SUDO cp "$key" "$CERT_DIR/bd.key"
  fix_cert_ownership
  chmod 0644 "$CERT_DIR/bd.crt" 2>/dev/null || true
  chmod 0600 "$CERT_DIR/bd.key" 2>/dev/null || true
  REACH_HOST="$sn"
  say "copied your cert into docker/certs/"
}

ensure_certs() {
  say "== Step 3/4: TLS cert (CS:${PORTS[CS]} / DS:${PORTS[DS]} / RMQ-wss:${PORTS[RABBIT_WSS]}) =="
  if cert_is_valid; then
    local cn; cn="$(openssl x509 -noout -subject -in "$CERT_DIR/bd.crt" 2>/dev/null | sed -E 's/.*CN ?= ?//; s/,.*//')"
    REACH_HOST="${cn:-$REACH_HOST}"
    say "a valid cert is already in docker/certs (CN=${cn:-unknown})."
    confirm "Keep it?" && { say; return 0; }
  fi
  cat <<EOF
Cert source for nginx (one cert covers CS, DS, and RabbitMQ wss):
  1) Tailscale          private/LAN host on a tailnet — real LE cert for the
                        *.ts.net name, no public IP or open ports (how BD is set up)
  2) Let's Encrypt      public host with a DNS name and port 80 reachable+free
  3) I already have one  reuse a cert+key on disk (e.g. one MitesBackend issued)
EOF
  case "$(ask 'Choose [1/2/3]: ')" in
    1) cert_tailscale ;;
    2) cert_certbot ;;
    3) cert_existing ;;
    *) die "pick 1, 2, or 3" ;;
  esac
  cert_is_valid || die "no usable cert at docker/certs/bd.crt — cannot bring up nginx with TLS."
  say
}

# ------------------------------------------------------------------------------
# 4. Bring up + bootstrap + verify.
# ------------------------------------------------------------------------------
bring_up() {
  say "== Step 4/4: build, start, bootstrap =="
  $DC up -d --build

  # Wait for the app containers to report healthy (compose healthchecks already
  # gate dependencies; this just makes the script block until usable).
  local tries=60
  say "waiting for services to become healthy ..."
  while (( tries-- > 0 )); do
    local unhealthy
    unhealthy="$($DC ps --format '{{.Service}} {{.Health}}' 2>/dev/null \
                  | grep -E ' (starting|unhealthy)$' || true)"
    [[ -z "$unhealthy" ]] && break
    sleep 3
  done
  $DC ps

  say
  say "creating admin user + registering ds1 ..."
  ./bootstrap_admin.sh || warn "bootstrap_admin.sh reported an issue — see its output above."
}

summarize() {
  local cs="${PORTS[CS]}" ds="${PORTS[DS]}" wss="${PORTS[RABBIT_WSS]}"
  cat <<EOF

================ BuildingDepot is up ================
CentralService : https://${REACH_HOST}:${cs}
DataService    : https://${REACH_HOST}:${ds}
RabbitMQ wss   : wss://${REACH_HOST}:${wss}/ws   (web-STOMP; BD-token auth)
Mailpit inbox  : http://localhost:8025           (dev signup/reset mail)

The admin credentials were printed by bootstrap_admin.sh just above
(admin@buildingdepot.org / <temp>, change on first login).

Renew the cert later by re-running:  sudo ./refresh-cert.sh   (reloads nginx)
Useful: '$DC ps', '$DC logs -f bd-central', '$DC down' (keep data) / 'down -v' (wipe).
EOF
  if [[ "${CODEPLOY:-0}" == 1 ]]; then
    cat <<EOF

Co-deploy note: another service is already listening on 80/443 here. BD was
left entirely off those ports — it publishes only ${cs}/${ds}/${wss} and adds no
host-level redirect, so that service (whatever it is) was not disturbed. If you
also want a front proxy ahead of BD, point it at these ports; don't move BD onto
80/443.
EOF
  fi
}

main() {
  say "BuildingDepot — guided docker setup"
  say "(detects tools, never installs; fills only what's missing; safe to re-run)"
  say
  need docker  "install Docker Engine / Podman with the docker CLI"
  need openssl "install openssl (used to generate .env secrets)"
  pick_compose

  ensure_env
  choose_ports
  ensure_certs
  bring_up
  summarize
}

main "$@"
