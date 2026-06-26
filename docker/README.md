# BuildingDepot — Docker Compose

Dev/test stack. Brings up Mongo + Redis + InfluxDB 1.8 + RabbitMQ + the three BD app processes (CentralReplica XML-RPC, CentralService gunicorn, DataService gunicorn) behind nginx.

## Quick start

Fastest — the guided script walks all of it (fills `.env` secrets, provisions the cert, brings the stack up, creates the admin user):

```bash
cd docker
./setup.sh
```

It only detects tools, it does not install them, so on a vanilla host install `docker` + `openssl` first (and `tailscale` or `certbot` for the cert step). It is safe to re-run after a crash — it fills only what is missing and never regenerates secrets the data volumes were created with. See "Guided setup" below.

Or do the same steps by hand:

```bash
cd docker
cp .env.example .env
# edit .env — at minimum replace every `replace-me`
# provision TLS certs into docker/certs (required for nginx + RabbitMQ wss); see "TLS" below
sudo CERT_PROVIDER=tailscale ./refresh-cert.sh   # or CERT_PROVIDER=certbot BD_CERT_DOMAIN=...
docker compose up -d --build
./bootstrap_admin.sh         # creates admin@buildingdepot.org + registers ds1
```

Then:

- CentralService — `https://localhost:81`
- DataService — `https://localhost:82`
- Mailpit inbox — `http://localhost:8025`

## Guided setup (`setup.sh`)

`./setup.sh` is the interactive equivalent of the manual steps above, meant for a fresh host. It:

1. Creates `docker/.env` from the example and generates each secret with `openssl rand -hex 32`, filling only placeholders so an existing `.env` is left as-is.
2. Checks the host ports the stack publishes and offers a rootless-engine remap (`81/82` → `8081/8082`) when needed.
3. Asks for a cert source — Tailscale, Let's Encrypt, or a cert you already hold — and drives `refresh-cert.sh` to provision `certs/bd.crt` + `bd.key` (one cert fronts CS:81, DS:82, and RabbitMQ wss:15675).
4. Builds and starts the stack, waits for health, and runs `bootstrap_admin.sh`.

It **detects** tools and never installs them; if something is missing it tells you exactly what. It is **idempotent** — re-running after a crash repeats the steps without regenerating secrets, reissuing a still-valid cert, or flagging the stack's own ports as conflicts.

**Co-located with another service?** The stack only ever publishes `81/82/15675` (plus `5672/15672/15674/8025`) and adds no host-level redirect — it never binds `80` or `443`. So it coexists with a reverse proxy already on the host (for example one fronting another backend on `443`). The one exception is the Let's Encrypt path: `certbot --standalone` wants port `80`, so if a proxy already holds it, use the Tailscale or bring-your-own-cert option instead — the script detects this and says so.

## Email (dev SMTP)

CentralService emails a temporary password on signup and password reset. There is no real mail server in dev, so a [Mailpit](https://mailpit.axllent.org/) container catches every message — read them at `http://localhost:8025` instead of an inbox.

How it is wired:

- `helper.py` sends via `SMTP_HOST:SMTP_PORT` (default `localhost:25`).
- `.env` sets `SMTP_HOST=mailpit` / `SMTP_PORT=1025`; `entrypoint.sh` renders them into `bd_settings.cfg`.
- The `mailpit` service listens on `1025` (SMTP) and `8025` (web inbox).

To get a usable password for a user: `POST /oauth/reset {email}`, open Mailpit, copy the temp password, then `POST /oauth/confirmReset {email, temp_password, new_password}`. Leave `SMTP_HOST`/`SMTP_PORT` unset to fall back to a local mailer.

## TLS (reverse proxy)

nginx terminates TLS on **81 (CS)** and **82 (DS)** so clients keep using `https://<host>:81` / `:82` unchanged. nginx only reads `certs/bd.crt` + `certs/bd.key`; how those PEMs are issued is `refresh-cert.sh`'s job, and it supports two scenarios. `certs/` holds the PEMs and is git-ignored. The connecting hostname must match the cert's name in both cases.

First cutover, either way, is the same once the cert exists:

```bash
cd docker
sudo CERT_PROVIDER=... [BD_CERT_DOMAIN=...] ./refresh-cert.sh   # writes certs/bd.crt + bd.key
docker compose up -d --force-recreate nginx                    # load the TLS config
```

### Public IP -> Let's Encrypt (certbot)

For a host with a public IP and a real domain whose A record points at it. certbot gets the cert over HTTP-01 (needs port 80 free and reachable), and the script copies the PEMs into `certs/`.

```bash
sudo apt install certbot
cd docker
sudo BD_CERT_DOMAIN=bd.example.com CERTBOT_EMAIL=you@example.com CERT_PROVIDER=certbot ./refresh-cert.sh
docker compose up -d --force-recreate nginx
```

Reach BD at `https://bd.example.com:81` / `:82`. Renewal is handled by certbot's own systemd timer; add a deploy hook so it recopies + reloads after each renew:

```bash
sudo certbot renew --deploy-hook "/path/to/docker/refresh-cert.sh"
```

(For a host behind NAT/CGNAT with a public domain, use a certbot DNS-01 plugin instead of `--standalone`; the copy + reload step is identical.)

### Private / no public IP -> Tailscale (default)

For a host with no public IP. The cert comes from Tailscale for the node's MagicDNS name (Let's Encrypt backed, validated over the `ts.net` DNS), so no public IP, owned domain, or open ports are needed. Requires `tailscale up` and HTTPS certs enabled in the tailnet admin console.

```bash
cd docker
sudo ./refresh-cert.sh                        # CERT_PROVIDER defaults to tailscale
docker compose up -d --force-recreate nginx
```

Reach BD at `https://<node>.<tailnet>.ts.net:81` / `:82`. Certs are 90-day; run `refresh-cert.sh` on a daily systemd timer or cron to auto-renew (it reloads nginx). WireGuard already encrypts the transport, so this TLS is mainly so browsers get a trusted `https://`.

### Live data over wss (RabbitMQ web-STOMP)

Browsers stream live sensor data over web-STOMP, and an `https://` page can only open a `wss://` socket. **nginx terminates that TLS on 15675** and proxies to RabbitMQ's plain web-STOMP listener on **15674** (`nginx.conf`); the broker itself speaks only plain `ws`. This keeps a single TLS termination point and, deliberately, keeps the private key out of the broker: nginx already reads `certs/bd.crt` / `bd.key` as root, whereas the RabbitMQ node runs as the unprivileged `rabbitmq` user — handing it the key would mean either a world-readable key or fighting the container-user/host-user UID mapping (which differs between Docker and rootless Podman). Plain `ws://` on 15674 stays available for in-network use. Point the UI at `wss://<node>.<tailnet>.ts.net:15675/ws` (`PUBLIC_RABBITMQ_HOSTNAME` = the node name, `PUBLIC_RABBITMQ_PORT` = 15675).

## RabbitMQ access (BD token as the broker credential)

Clients authenticate to RabbitMQ with a **BuildingDepot OAuth token**, not a broker password. A client connects with its email as the login and its BD token as the passcode, and RabbitMQ asks CentralService whether that token may read a given sensor. So there is one token and one authority: BD owns permissions, the broker just enforces them. No shared broker password is handed to browsers.

This is on by default from a fresh `docker compose up`. The two plugins (`rabbitmq_auth_backend_http`, `rabbitmq_auth_backend_cache`) ship in `rabbitmq-enabled-plugins`, and the backend chain plus the four CentralService endpoints are configured in `rabbitmq.conf`. RabbitMQ tries its internal backend first (so `bdadmin`, used for ops and the ingest publisher, is unchanged) and falls back to the HTTP backend for everyone else. Adding it is purely additive.

Connecting as a user (for example over STOMP or web-STOMP):

```
login:    <user email>
passcode: <BD OAuth access token>
host:     /
```

Subscribe to `/exchange/master_exchange/<sensor_id>`. The subscription is allowed only if BD's ACL grants that user read on that sensor.

Two setup-flow notes:

- **`master_exchange` is now a `topic` exchange** (it was `direct`). Per-sensor authorization needs the topic exchange so RabbitMQ runs its per-routing-key check. A fresh deployment creates it as `topic` on the first publish, nothing to do. An existing deployment that already has a `direct` `master_exchange` must delete it once so it is recreated as `topic` (`rabbitmqctl delete exchange master_exchange`, or `docker compose down -v` in dev).
- **Token auth needs `bd-central` reachable.** RabbitMQ calls CentralService to authorize, with a short cache. Internal users (`bdadmin`) keep working even if BD is down; token users cannot connect until BD is up. There is no compose `depends_on` from rabbitmq to bd-central (that would be a cycle), and none is needed since auth happens on client connect, by which point BD is up.

Design and rationale: `docs/rabbitmq-auth.md`.

## Running under rootless Podman

The stack also runs under rootless Podman (via `podman-docker`, so the `docker compose` commands above work unchanged). Two host-level adjustments are needed because rootless containers run in a user namespace.

### 1. Network backend — use slirp4netns instead of pasta

Podman's default rootless network helper is `pasta`. On some distros the packaged `passt`/`pasta` binary segfaults at startup (seen on Ubuntu *resolute* with glibc 2.43 and the `git20260120` passt snapshot — `pasta --version` itself crashes), which makes every container fail at the networking step:

```
Error response from daemon: setting up Pasta: pasta failed with exit code -1
```

Switch the rootless backend to `slirp4netns` (Podman's previous default; fully supported, just slightly lower throughput). Create `~/.config/containers/containers.conf`:

```ini
[network]
default_rootless_network_cmd = "slirp4netns"
```

Then `docker compose up -d` works. This is a per-user setting. Once a fixed `passt` lands (`apt upgrade passt`), you can delete this override to go back to pasta.

### 2. Privileged ports (81/82)

Rootless containers cannot bind host ports below 1024, so publishing CS/DS on **81/82** fails with:

```
rootlessport cannot expose privileged port 81 ... bind: permission denied
```

Pick one:

- **Lower the threshold (keeps the :81/:82 URLs).** Persist it so it survives reboots:
  ```bash
  echo 'net.ipv4.ip_unprivileged_port_start=80' | sudo tee /etc/sysctl.d/50-bd-ports.conf
  sudo sysctl --system
  ```
  This is host-wide. (`sudo sysctl -w net.ipv4.ip_unprivileged_port_start=80` sets it for the current boot only.)

- **Remap to unprivileged ports (no root, self-contained).** In `.env` set e.g. `HOST_PORT_CS=8081` and `HOST_PORT_DS=8082` (and `HOST_PORT_RABBIT_WSS` ≥ 1024 if you also hit it). Reach BD at `https://<host>:8081` / `:8082` instead. The container-internal ports and `nginx.conf` are unaffected.

## Notes

- **InfluxDB 1.8** — BD pins `influxdb-python==5.3.1` which speaks the v1 line protocol. Do not bump to 2.x without porting the BD client.
- **Secrets at container start, not build time.** `entrypoint.sh` renders `bd_settings.cfg` and `CentralReplica/config.py` from env. The image has no secrets baked in.
- **TLS is terminated at nginx (81/82).** Provision `certs/bd.crt` + `certs/bd.key` (via `refresh-cert.sh`) before relying on HTTPS/wss.
- **Volumes** are named (`mongo-data`, `redis-data`, `influx-data`, `rabbit-data`). Survive `docker compose down`; wiped by `docker compose down -v`.
