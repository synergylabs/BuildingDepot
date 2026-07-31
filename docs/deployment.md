Slop warning: doc is LLM-written and written primarily for LLM consumption.
Humans may read but information may be confusing or poorly-communicated.

# Deployment

BuildingDepot runs bare metal: the three BD Python services under systemd user
units (via uv + gunicorn), Valkey and RabbitMQ from apt. Only the two datastores
that cannot come from apt — MongoDB 7 and InfluxDB 1.8 — run in containers, and
those publish to loopback only. A **host nginx** terminates TLS in front. TLS
lives on the host so one nginx can front BD alongside other co-located services.

- CentralService (CS): `https://<host>:81` -> `127.0.0.1:8081`
- DataService (DS): `https://<host>:82` -> `127.0.0.1:8082`
- RabbitMQ web-STOMP wss: `wss://<host>:15675/ws` -> `127.0.0.1:15674` (plain ws)

## Install

From the repo root:

```bash
git clone <repo-url> && cd BuildingDepot
python3 deploy/install.py
```

`deploy/install.py` provisions the repo-root `.env` from `.env.example`
(generating fresh infra secrets), installs `valkey-server` + `rabbitmq-server`,
syncs Python deps with uv, brings up the datastore containers, configures Valkey
and RabbitMQ, installs the three systemd user units, and runs
`deploy/bootstrap_bare.py`. Flags: `--no-service`, `--no-bootstrap`,
`--force-env`, `--no-ask-sudo`, `--dev`.

The admin credential (`admin@buildingdepot.org` + a generated temp password) is
printed by the bootstrap step — change it on first login.

### What bootstrap seeds

BD cannot start from a genuinely empty database, so `bootstrap_bare.py` upserts
three records. Every step is idempotent, so re-running is safe.

- **The admin user** — `admin@buildingdepot.org`, super role, `first_login` set,
  with the printed temporary password.
- **The `ds1` data service** — `host=127.0.0.1`, `port=8080`. CentralService
  looks this row up to find the replica's XML-RPC endpoint. Note the port is the
  **replica's** 8080, not DataService's 8082. Easy to miss, and nothing works
  without it.
- **The OAuth client** — `BD_CLIENT_ID` / `BD_CLIENT_SECRET` from `.env`, upserted
  as a client owned by the admin user. BD normally mints clients itself via
  `GET /oauth/client`, but a co-located MitesBackend needs the pair to exist
  before it first authenticates, so the pair is declared up front and registered
  here. BD's token endpoint only looks the pair up, so a declared client is
  equivalent to a minted one. Leave `BD_CLIENT_ID` blank to skip this and mint a
  client by hand instead.

Enable linger so the user units survive logout:

```bash
sudo loginctl enable-linger $USER
```

## Configuration

Everything site-specific lives in **one** gitignored, chmod-600 file: `.env` at
the repo root. `buildingdepot/bd_config.py` reads it and hands the values to
Flask; `deploy/compose.yml` reads the same file for the Mongo and Influx
credentials, so the apps and the stores cannot drift apart.

The `.env` keys are the Flask config keys verbatim (`MONGODB_PWD`,
`RABBITMQ_ADMIN_PWD`, …), so nothing maps names between layers. Precedence is
process environment, then `.env`, then the defaults in `bd_config.py`. Point
elsewhere with `BD_ENV=/path/to/env`.

Structural values are **not** env keys — database names, `NAME=ds1`, and the
default `127.0.0.1` hosts/ports are defaults in `bd_config.py`. Required secrets
(`SECRET_KEY`, `MONGODB_PWD`, `REDIS_PWD`, `INFLUXDB_PWD`, `RABBITMQ_ADMIN_PWD`,
`RABBITMQ_ENDUSER_PWD`) have no default: a missing or still-`replace-me` value
raises at service start rather than failing later inside a database driver.

Changing a credential means editing `.env`, restarting the affected service
(`systemctl --user restart bd-central bd-data bd-replica`), and — for a datastore
password — reconfiguring the store itself, which `install.py` does for Valkey and
RabbitMQ on a re-run.

## HTTPS via the host reverse proxy

The host nginx tooling is vendored under `deploy/shared/`. Run it as root:
install the shared base config once per host, then enable BD's site fragment
(which covers all three servers — 81, 82, 15675).

```bash
# Once per host: nginx + shared base config (websocket map, TLS params).
sudo python3 deploy/shared/host.py install

# Per app: provision a cert and enable the BD site fragment.
sudo python3 deploy/shared/host.py enable deploy/nginx/buildingdepot.conf \
    --domain <host> --cert <tailscale|http|dns-cloudflare> [options]
```

`enable` renders the fragment's `{{ DOMAIN }}` / `{{ SSL_CERT }}` /
`{{ SSL_KEY }}` placeholders (the same cert serves CS, DS, and wss), symlinks
into `sites-enabled/`, runs `nginx -t`, and reloads. The connecting hostname
must match the cert's name.

### Cert sources

Three issuers, selected with `--cert`:

- **tailscale** (how the BD box is set up) — a host with no public IP but on
  your tailnet; `--domain` auto-detected from `tailscale status`. Needs
  MagicDNS + HTTPS Certificates enabled in the tailnet admin console. Reach BD
  at `https://<node>.<tailnet>.ts.net:81` / `:82`.
- **http** — a host with a real domain. HTTP-01 on `:80` by default.
  (`letsencrypt` accepted as legacy alias.)
- **dns-cloudflare** — DNS-01 via the Cloudflare API. Works behind NAT/CGNAT.
  Pass `--cloudflare-token` or set `CF_DNS_API_TOKEN`.

Full walkthroughs (Tailscale prerequisites and renewal, certbot HTTP-01,
DNS-01 via Cloudflare):
[`deploy/shared/docs/certificates.md`](../deploy/shared/docs/certificates.md).

## Live data over wss (RabbitMQ web-STOMP)

Browsers stream live sensor data over web-STOMP, and an `https://` page can only
open a `wss://` socket. The host nginx terminates that TLS on **15675** and
proxies to RabbitMQ's plain web-STOMP listener on **15674**; the broker itself
speaks only plain `ws`. This keeps a single TLS termination point and keeps the
private key out of the broker. Point the UI at `wss://<host>:15675/ws`
(`PUBLIC_RABBITMQ_HOSTNAME` = the host name, `PUBLIC_RABBITMQ_PORT` = 15675).

## RabbitMQ access (BD token as the broker credential)

Clients authenticate to RabbitMQ with a **BuildingDepot OAuth token**, not a
broker password. A client connects with its email as the login and its BD token
as the passcode, and RabbitMQ asks CentralService whether that token may read a
given sensor. So there is one token and one authority: BD owns permissions, the
broker just enforces them. No shared broker password is handed to browsers.

`install.py` sets this up. The two plugins (`rabbitmq_auth_backend_http`,
`rabbitmq_auth_backend_cache`) are enabled via `deploy/rabbitmq/enabled_plugins`,
and the backend chain plus the four CentralService endpoints are configured in
`deploy/rabbitmq/rabbitmq.conf`. RabbitMQ tries its internal backend first (so
`bdadmin`, used for ops and the ingest publisher, is unchanged) and falls back to
the HTTP backend for everyone else. Adding it is purely additive.

Connecting as a user (for example over STOMP or web-STOMP):

```
login:    <user email>
passcode: <BD OAuth access token>
host:     /
```

Subscribe to `/exchange/master_exchange/<sensor_id>`. The subscription is allowed
only if BD's ACL grants that user read on that sensor.

Two setup-flow notes:

- **`master_exchange` is a `topic` exchange** (it was `direct`). Per-sensor
  authorization needs the topic exchange so RabbitMQ runs its per-routing-key
  check. A fresh deployment creates it as `topic` on the first publish, nothing
  to do. An existing deployment that already has a `direct` `master_exchange`
  must delete it once so it is recreated as `topic`
  (`rabbitmqctl delete exchange master_exchange`).
- **Token auth needs `bd-central` reachable.** RabbitMQ calls CentralService to
  authorize, with a short cache. Internal users (`bdadmin`) keep working even if
  BD is down; token users cannot connect until BD is up. Auth happens on client
  connect, so ordering at boot does not matter.

## Email

CentralService emails a temporary password on signup and password reset, sending
via `SMTP_HOST:SMTP_PORT` from `.env` (default `localhost:25`).

For dev there is no real mail server, so `python3 deploy/install.py --dev` runs a
[Mailpit](https://mailpit.axllent.org/) container that catches every message —
read them at `http://localhost:8025`. Point BD at it with `SMTP_PORT=1025` in
`.env`.

To get a usable password for a user: `POST /oauth/reset {email}`, open Mailpit,
copy the temp password, then `POST /oauth/confirmReset {email, temp_password,
new_password}`.

Set `EMAIL=GMAIL` with `CLIENT_ID` / `CLIENT_SECRET` / `REFRESH_TOKEN` in `.env`
to relay through the Gmail API instead.

## Day to day

Logs come from the journal:

```bash
journalctl --user -u bd-central -f
journalctl --user -u bd-data -f
journalctl --user -u bd-replica -f
docker compose -f deploy/compose.yml logs
```

Check the stack is serving:

```bash
curl -s -o /dev/null -w "CS %{http_code}\n" http://127.0.0.1:8081/auth/login
curl -s -o /dev/null -w "DS %{http_code}\n" http://127.0.0.1:8082/
```

Datastore state lives in the named volumes `mongo-data` and `influx-data`, which
survive `docker compose down`; `down -v` wipes them. Valkey persists to its own
apt-managed data directory with `appendonly yes`.

`install.py` is idempotent — re-run it after changing `.env` or bumping deps. It
leaves an existing `.env` alone unless you pass `--force-env`.

## Notes

- **InfluxDB 1.8** — BD pins `influxdb-python==5.3.1`, which speaks the v1 line
  protocol. Do not bump to 2.x without porting the BD client.
- **uv** — the systemd units invoke uv by absolute path, resolved by
  `install.py` at install time. Re-run `install.py` if uv moves.
