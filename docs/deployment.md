# Deployment

BuildingDepot runs as a Docker Compose stack (Mongo, Redis, InfluxDB 1.8,
RabbitMQ, and the three BD processes). The app ports are published to host
loopback; a **host nginx** terminates TLS in front of them. TLS lives on the
host (not in the container) so one nginx can front BD alongside other
co-located services, and the private key never enters the container.

- CentralService (CS): `https://<host>:81` -> `127.0.0.1:8081`
- DataService (DS): `https://<host>:82` -> `127.0.0.1:8082`
- RabbitMQ web-STOMP wss: `wss://<host>:15675/ws` -> `127.0.0.1:15674` (plain ws)

## Install

From the repo root:

```bash
git clone <repo-url> && cd BuildingDepot
python3 deploy/install.py        # provision docker/.env, build + up, bootstrap
```

`deploy/install.py` provisions `deploy/docker/.env` from `.env.example`
(generating fresh infra secrets), builds and starts the stack, and runs
`bootstrap_admin.sh` to create the admin user and register the `ds1` data
service. Flags: `--no-build`, `--no-bootstrap`, `--force-env`.

The admin credential (`admin@buildingdepot.org` + a generated temp password) is
printed by the bootstrap step — change it on first login.

## HTTPS via the host reverse proxy

The host nginx tooling is vendored under `deploy/shared/`. Run it as root:
install the shared base config once per host, then enable BD's site fragment
(which covers all three servers — 81, 82, 15675).

```bash
# Once per host: nginx + shared base config (websocket map, TLS params).
sudo python3 deploy/shared/host.py install

# Per app: provision a cert and enable the BD site fragment.
sudo python3 deploy/shared/host.py enable deploy/nginx/buildingdepot.conf \
    --domain <host> --cert <tailscale|letsencrypt> [options]
```

`enable` renders the fragment's `{{ DOMAIN }}` / `{{ SSL_CERT }}` /
`{{ SSL_KEY }}` placeholders (the same cert serves CS, DS, and wss), symlinks
into `sites-enabled/`, runs `nginx -t`, and reloads. The connecting hostname
must match the cert's name.

### Cert sources

Two issuers, selected with `--cert`:

- **tailscale** (how the BD box is set up) — a host with no public IP but on
  your tailnet; `--domain` auto-detected from `tailscale status`. Needs
  MagicDNS + HTTPS Certificates enabled in the tailnet admin console. Reach BD
  at `https://<node>.<tailnet>.ts.net:81` / `:82`.
- **letsencrypt** — a host with a real domain. HTTP-01 on `:80` by default, or
  a DNS-01 plugin via repeated `--certbot-auth-arg` flags when `:80` isn't
  reachable (NAT/CGNAT).

Full walkthroughs (Tailscale prerequisites and renewal, certbot HTTP-01,
DNS-01 plugin setup):
[`deploy/shared/docs/certificates.md`](../deploy/shared/docs/certificates.md).

## Live data over wss (RabbitMQ web-STOMP)

Browsers stream live sensor data over web-STOMP, and an `https://` page can only
open a `wss://` socket. The host nginx terminates that TLS on **15675** and
proxies to RabbitMQ's plain web-STOMP listener on **15674**; the broker itself
speaks only plain `ws`. This keeps a single TLS termination point and keeps the
private key out of the broker. Point the UI at `wss://<host>:15675/ws`
(`PUBLIC_RABBITMQ_HOSTNAME` = the host name, `PUBLIC_RABBITMQ_PORT` = 15675).

## More

See the compose-stack details (email, RabbitMQ token auth, rootless Podman) in
[`deploy/docker/README.md`](../deploy/docker/README.md) and the internals in
[`docs/docker-implementation.md`](docker-implementation.md).
