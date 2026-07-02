<!-- vendored deploy library — do not edit here; regenerate from the deploy source. -->

# Certificate provisioning (`host.py enable --cert ...`)

`host.py enable` provisions a real certificate — Tailscale or Let's Encrypt,
never self-signed in production — before enabling a site fragment. `certs.py`
implements the two issuers, selected with `--cert`. Certs land in
`/etc/nginx/certs/<site>.{crt,key}` (tailscale) or under
`/etc/letsencrypt/live/<domain>/` (letsencrypt); keys are chmod 600. The
connecting hostname must match the cert's name.

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

## Public IP + domain → Let's Encrypt (certbot, HTTP-01)

For a host with a public IP and a real domain whose A/AAAA record points at it.
certbot validates over HTTP-01 (needs port 80 free and reachable).

```bash
sudo apt install certbot
sudo python3 deploy/shared/host.py enable deploy/nginx/<app>.conf \
    --domain app.example.com --cert letsencrypt --email you@example.com
```

certbot installs its own renewal timer.

## Behind NAT/CGNAT → Let's Encrypt (certbot, DNS-01 plugin)

For a host with a real domain but no reachable port 80 (NAT, CGNAT,
firewalled), validate over DNS-01 instead. certbot proves control by writing a
TXT record through your DNS provider's API, so nothing needs to be
inbound-reachable. Cloudflare is shown; the same pattern works for any
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
sudo python3 deploy/shared/host.py enable deploy/nginx/<app>.conf \
    --domain app.example.com --cert letsencrypt --email you@example.com \
    --certbot-auth-arg --dns-cloudflare \
    --certbot-auth-arg --dns-cloudflare-credentials \
    --certbot-auth-arg /root/.secrets/cloudflare.ini
```

certbot records the authenticator + credentials path in the renewal config at
first issue, so `certbot renew` reuses the DNS plugin automatically.
