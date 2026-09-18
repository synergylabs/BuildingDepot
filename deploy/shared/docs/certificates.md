<!-- vendored deploy library; do not edit here; regenerate from the deploy source. -->

# HTTPS certificates

Slop warning: text is LLM-written.

Use `host.py enable` to obtain a trusted certificate and publish one nginx site.
The hostname in `--domain` must match the certificate.

Run the following from the relevant repository.
Use `Mites-Deploy/shared/host.py` from the deployment repository.
Use `deploy/shared/host.py` from an application repository.

Install the shared nginx configuration once per host:

```bash
cd /path/to/Mites-Deploy
sudo python3 shared/host.py install
```

Run `enable` once for each nginx site.
Run it again only after changing a site, domain, certificate mode, or certificate.

Choose one certificate mode.

## Tailscale

Use this mode for a private host on your tailnet.
Enable MagicDNS and HTTPS Certificates in the Tailscale admin console first.

```bash
cd /path/to/<service>
sudo python3 deploy/shared/host.py enable deploy/nginx/<app>.conf \
    --domain <node>.<tailnet>.ts.net --cert tailscale
```

Re-run the command before the 90-day certificate expires.

## Public domain

Use `http` when the domain points to this host and port 80 is reachable.

```bash
cd /path/to/<service>
sudo python3 deploy/shared/host.py enable deploy/nginx/<app>.conf \
    --domain app.example.com --cert http --email you@example.com
```

Certbot installs a renewal timer.

## Cloudflare DNS

Use `dns-cloudflare` when port 80 is not reachable.
Create a Cloudflare API token with `Zone:DNS:Edit` and `Zone:Zone:Read` on the
relevant zone.
Do not use the Global API Key.

Pass the token through `sudo` so it does not appear in the process arguments:

```bash
cd /path/to/<service>
sudo CF_DNS_API_TOKEN="$CF_DNS_API_TOKEN" \
  python3 deploy/shared/host.py enable deploy/nginx/<app>.conf \
  --domain app.example.com --cert dns-cloudflare --email you@example.com
```

Store the token in `site.env` for a multi-service deployment.
The installer stores it in `/etc/letsencrypt/cloudflare.ini` with restricted
permissions and configures renewal.

Replace `<app>` with the service name and repeat the enable command for each site.
