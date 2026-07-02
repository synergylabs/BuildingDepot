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
sudo python3 deploy/shared/host.py enable deploy/nginx/buildingdepot.conf.sample \
    --domain <host> --cert <tailscale|letsencrypt> [options]
```

`enable` renders the fragment's `{{ DOMAIN }}` / `{{ SSL_CERT }}` /
`{{ SSL_KEY }}` placeholders (the same cert serves CS, DS, and wss), symlinks
into `sites-enabled/`, runs `nginx -t`, and reloads. The connecting hostname
must match the cert's name.

### Private / no public IP -> Tailscale (default)

For a host with no public IP but on your tailnet. The cert comes from Tailscale
for the node's MagicDNS name (Let's Encrypt backed, validated over `ts.net`
DNS). Requires `tailscale up` and HTTPS certs enabled in the tailnet admin
console.

```bash
sudo python3 deploy/shared/host.py enable deploy/nginx/buildingdepot.conf.sample \
    --cert tailscale          # --domain auto-detected from `tailscale status`
```

Reach BD at `https://<node>.<tailnet>.ts.net:81` / `:82`. Tailscale certs are
90-day; re-run on a daily timer to renew (it reloads nginx).

### Public IP + domain -> Let's Encrypt (certbot, HTTP-01)

For a host with a public IP and a real domain whose A record points at it.
certbot validates over HTTP-01 (needs port 80 free and reachable).

```bash
sudo apt install certbot
sudo python3 deploy/shared/host.py enable deploy/nginx/buildingdepot.conf.sample \
    --domain bd.example.com --cert letsencrypt --email you@example.com
```

certbot installs its own renewal timer.

### Behind NAT/CGNAT -> Let's Encrypt (certbot, DNS-01 plugin)

For a host with a real domain but no reachable port 80 (NAT, CGNAT, firewalled),
validate over DNS-01 instead. certbot proves control by writing a TXT record
through your DNS provider's API, so nothing needs to be inbound-reachable.
Cloudflare is shown; the same pattern works for any
[certbot DNS plugin](https://eff-certbot.readthedocs.io/en/stable/using.html#dns-plugins)
(Route 53, Google, DigitalOcean, …) — swap the `--dns-*` flags.

```bash
# 1. Install the plugin (matches your certbot install method)
sudo apt install python3-certbot-dns-cloudflare

# 2. Drop the API token where certbot can read it. Use a scoped Cloudflare token
#    with Zone:DNS:Edit on the relevant zone (not the global API key).
sudo install -d -m 700 /root/.secrets
printf 'dns_cloudflare_api_token = %s\n' "$CF_TOKEN" | sudo tee /root/.secrets/cloudflare.ini >/dev/null
sudo chmod 600 /root/.secrets/cloudflare.ini

# 3. Issue, pointing the authenticator at the plugin (repeat --certbot-auth-arg
#    per token). Add `--certbot-auth-arg --dns-cloudflare-propagation-seconds`
#    `--certbot-auth-arg 30` if DNS needs a moment to propagate.
sudo python3 deploy/shared/host.py enable deploy/nginx/buildingdepot.conf.sample \
    --domain bd.example.com --cert letsencrypt --email you@example.com \
    --certbot-auth-arg --dns-cloudflare \
    --certbot-auth-arg --dns-cloudflare-credentials \
    --certbot-auth-arg /root/.secrets/cloudflare.ini
```

certbot records the authenticator + credentials path in the renewal config at
first issue, so `certbot renew` reuses the DNS plugin automatically.

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
