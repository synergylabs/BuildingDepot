<!-- vendored deploy library — do not edit here; regenerate from the deploy source. -->

# Certificate provisioning (`host.py enable --cert ...`)

`host.py enable` provisions a real certificate — Tailscale or Let's Encrypt,
never self-signed in production — before enabling a site fragment. `certs.py`
implements the issuers, selected with `--cert`. Certs land in
`/etc/nginx/certs/<site>.{crt,key}` (tailscale) or under
`/etc/letsencrypt/live/<domain>/` (http, dns-cloudflare); keys are chmod 600.
The connecting hostname must match the cert's name.

certbot (and the Cloudflare DNS plugin when needed) is installed automatically
via apt on first use — no manual `apt install` required.

The examples below use a placeholder fragment path — substitute this app's
`deploy/nginx/<app>.conf`.

## Private / no public IP → Tailscale

For a host with no public IP but on your tailnet. The cert comes from Tailscale
for the node's MagicDNS name (Let's Encrypt backed, validated over `ts.net`
DNS), so it is real and publicly trusted. One-time: enable **MagicDNS** and
**HTTPS Certificates** in the tailnet admin console, and `tailscale up` on the
host.

```bash
sudo python3 deploy/shared/host.py enable deploy/nginx/<app>.conf \
    --cert tailscale          # --domain auto-detected from `tailscale status`
```

Tailscale certs are 90-day; re-run on a timer to renew (it reloads nginx).

## Public IP + domain → HTTP-01 (`--cert http`)

For a host with a public IP and a real domain whose A/AAAA record points at it.
certbot validates over HTTP-01 (needs port 80 free and reachable).

```bash
sudo python3 deploy/shared/host.py enable deploy/nginx/<app>.conf \
    --domain app.example.com --cert http --email you@example.com
```

certbot installs its own renewal timer (`certbot.timer`).

> **Note**: `--cert letsencrypt` is accepted as a legacy alias for `--cert http`.

## Behind NAT/CGNAT → DNS-01 via Cloudflare (`--cert dns-cloudflare`)

For a host with a real domain but no reachable port 80 (NAT, CGNAT,
firewalled). certbot proves domain control by writing a TXT record through the
Cloudflare API — nothing needs to be inbound-reachable.

### 1. Create a scoped Cloudflare API token

In the Cloudflare dashboard, create an API token with:
- **Zone / DNS / Edit** — on the relevant zone
- **Zone / Zone / Read** — on the relevant zone

Do **not** use the Global API Key.

### 2. Make the token available

Either set it in the environment:

```bash
export CF_DNS_API_TOKEN="your-token-here"
```

Or pass it directly:

```bash
--cloudflare-token "your-token-here"
```

In a multi-service deployment, add `CF_DNS_API_TOKEN` to `site.env`.

### 3. Issue the certificate

```bash
sudo python3 deploy/shared/host.py enable deploy/nginx/<app>.conf \
    --domain app.example.com --cert dns-cloudflare --email you@example.com
```

The token is written to `/etc/letsencrypt/cloudflare.ini` (chmod 600). certbot
records the authenticator + credentials path in the renewal config at first
issue, so `certbot renew` (via `certbot.timer`) reuses the DNS plugin
automatically.
