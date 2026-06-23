# BuildingDepot — Docker Compose

Dev/test stack. Brings up Mongo + Redis + InfluxDB 1.8 + RabbitMQ + the three BD app processes (CentralReplica XML-RPC, CentralService gunicorn, DataService gunicorn) behind nginx.

## Quick start

```bash
cd docker
cp .env.example .env
# edit .env — at minimum replace every `replace-me`
docker compose up -d --build
./bootstrap_admin.sh         # creates admin@buildingdepot.org + registers ds1
```

Then:

- CentralService — `http://localhost:81`
- DataService — `http://localhost:82`
- Mailpit inbox — `http://localhost:8025`

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

Browsers stream live sensor data over web-STOMP, and an `https://` page can only open a `wss://` socket. RabbitMQ serves that on **15675** using the same `certs/bd.crt` / `bd.key`, configured in `rabbitmq.conf`. Plain `ws://` stays on 15674 for in-network use. nginx runs as root so it reads the `0600` key, but the RabbitMQ node runs as the unprivileged `rabbitmq` user, so `refresh-cert.sh` sets the key world-readable (`0644`) after issuing it. That is fine on a single-user host; the key never leaves the box. Point the UI at `wss://<node>.<tailnet>.ts.net:15675/ws` (`PUBLIC_RABBITMQ_HOSTNAME` = the node name, `PUBLIC_RABBITMQ_PORT` = 15675).

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

## Notes

- **InfluxDB 1.8** — BD pins `influxdb-python==5.3.1` which speaks the v1 line protocol. Do not bump to 2.x without porting the BD client.
- **Secrets at container start, not build time.** `entrypoint.sh` renders `bd_settings.cfg` and `CentralReplica/config.py` from env. The image has no secrets baked in.
- **No TLS in this compose.** Add a real cert at the nginx layer for production.
- **Volumes** are named (`mongo-data`, `redis-data`, `influx-data`, `rabbit-data`). Survive `docker compose down`; wiped by `docker compose down -v`.
