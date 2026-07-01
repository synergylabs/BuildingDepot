# BuildingDepot — Docker Compose stack

Brings up Mongo + Redis + InfluxDB 1.8 + RabbitMQ + the three BD app processes
(CentralReplica XML-RPC, CentralService gunicorn, DataService gunicorn). App
ports are published to **host loopback**; the host nginx terminates TLS in front
of them (see [`../../docs/deployment.md`](../../docs/deployment.md)).

## Quick start

The normal path is `python3 deploy/install.py` from the repo root (provisions
`.env`, builds, brings up the stack, and bootstraps). To drive the stack
directly from this directory:

```bash
cp .env.example .env
# edit .env — at minimum replace every `replace-me`
docker compose up -d --build
./bootstrap_admin.sh         # admin user + ds1 data service
```

Then, over loopback:

- CentralService — `http://127.0.0.1:8081`
- DataService — `http://127.0.0.1:8082`
- Mailpit inbox — `http://localhost:8025`

For public HTTPS (`https://<host>:81` / `:82`, and `wss://<host>:15675/ws`),
enable the host nginx site fragment — see
[`../../docs/deployment.md`](../../docs/deployment.md). TLS is no longer part of
this stack.

## Email (dev SMTP)

CentralService emails a temporary password on signup and password reset. There
is no real mail server in dev, so a [Mailpit](https://mailpit.axllent.org/)
container catches every message — read them at `http://localhost:8025` instead
of an inbox.

How it is wired:

- `helper.py` sends via `SMTP_HOST:SMTP_PORT` (default `localhost:25`).
- `.env` sets `SMTP_HOST=mailpit` / `SMTP_PORT=1025`; `entrypoint.sh` renders them into `bd_settings.cfg`.
- The `mailpit` service listens on `1025` (SMTP) and `8025` (web inbox).

To get a usable password for a user: `POST /oauth/reset {email}`, open Mailpit,
copy the temp password, then `POST /oauth/confirmReset {email, temp_password,
new_password}`. Leave `SMTP_HOST`/`SMTP_PORT` unset to fall back to a local
mailer.

## Live data over wss (RabbitMQ web-STOMP)

Browsers stream live sensor data over web-STOMP, and an `https://` page can only
open a `wss://` socket. The **host nginx terminates that TLS on 15675** and
proxies to RabbitMQ's plain web-STOMP listener on **15674** (published to
loopback by this stack); the broker itself speaks only plain `ws`. This keeps a
single TLS termination point and keeps the private key out of the broker. Point
the UI at `wss://<host>:15675/ws` (`PUBLIC_RABBITMQ_HOSTNAME` = the host name,
`PUBLIC_RABBITMQ_PORT` = 15675). Cert setup is in
[`../../docs/deployment.md`](../../docs/deployment.md).

## RabbitMQ access (BD token as the broker credential)

Clients authenticate to RabbitMQ with a **BuildingDepot OAuth token**, not a
broker password. A client connects with its email as the login and its BD token
as the passcode, and RabbitMQ asks CentralService whether that token may read a
given sensor. So there is one token and one authority: BD owns permissions, the
broker just enforces them. No shared broker password is handed to browsers.

This is on by default from a fresh `docker compose up`. The two plugins
(`rabbitmq_auth_backend_http`, `rabbitmq_auth_backend_cache`) ship in
`rabbitmq-enabled-plugins`, and the backend chain plus the four CentralService
endpoints are configured in `rabbitmq.conf`. RabbitMQ tries its internal backend
first (so `bdadmin`, used for ops and the ingest publisher, is unchanged) and
falls back to the HTTP backend for everyone else. Adding it is purely additive.

Connecting as a user (for example over STOMP or web-STOMP):

```
login:    <user email>
passcode: <BD OAuth access token>
host:     /
```

Subscribe to `/exchange/master_exchange/<sensor_id>`. The subscription is
allowed only if BD's ACL grants that user read on that sensor.

Two setup-flow notes:

- **`master_exchange` is now a `topic` exchange** (it was `direct`). Per-sensor authorization needs the topic exchange so RabbitMQ runs its per-routing-key check. A fresh deployment creates it as `topic` on the first publish, nothing to do. An existing deployment that already has a `direct` `master_exchange` must delete it once so it is recreated as `topic` (`rabbitmqctl delete exchange master_exchange`, or `docker compose down -v` in dev).
- **Token auth needs `bd-central` reachable.** RabbitMQ calls CentralService to authorize, with a short cache. Internal users (`bdadmin`) keep working even if BD is down; token users cannot connect until BD is up. There is no compose `depends_on` from rabbitmq to bd-central (that would be a cycle), and none is needed since auth happens on client connect, by which point BD is up.

## Running under rootless Podman

The stack also runs under rootless Podman (via `podman-docker`, so the `docker
compose` commands above work unchanged). Because app ports are published to
loopback on unprivileged ports (8081/8082/15674), the privileged-port problem
that used to bite the in-container nginx is gone. One host-level adjustment may
still be needed:

Podman's default rootless network helper is `pasta`. On some distros the
packaged `passt`/`pasta` binary segfaults at startup (seen on Ubuntu *resolute*
with glibc 2.43 and the `git20260120` passt snapshot — `pasta --version` itself
crashes), which makes every container fail at the networking step:

```
Error response from daemon: setting up Pasta: pasta failed with exit code -1
```

Switch the rootless backend to `slirp4netns` (Podman's previous default; fully
supported, just slightly lower throughput). Create
`~/.config/containers/containers.conf`:

```ini
[network]
default_rootless_network_cmd = "slirp4netns"
```

Then `docker compose up -d` works. This is a per-user setting. Once a fixed
`passt` lands (`apt upgrade passt`), you can delete this override.

## Notes

- **InfluxDB 1.8** — BD pins `influxdb-python==5.3.1` which speaks the v1 line protocol. Do not bump to 2.x without porting the BD client.
- **Secrets at container start, not build time.** `entrypoint.sh` renders `bd_settings.cfg` and `CentralReplica/config.py` from env. The image has no secrets baked in.
- **TLS is terminated by the host nginx**, not this stack — see [`../../docs/deployment.md`](../../docs/deployment.md).
- **Volumes** are named (`mongo-data`, `redis-data`, `influx-data`, `rabbit-data`). Survive `docker compose down`; wiped by `docker compose down -v`.
