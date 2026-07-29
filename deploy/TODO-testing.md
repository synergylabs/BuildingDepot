# Bare-metal deploy — testing checklist

## Unit-level (no target host needed)

- [ ] Template rendering: run `template.render_file()` on both `.template` files
      with sample values, verify output matches expected `bd_settings.cfg` /
      `config.py`. No missing placeholders, no `{{ }}` leftovers.
- [ ] Env provisioning: run `manifest.apply_site_env()` with and without a
      manifest. Verify secrets generated, manifest keys mapped, existing `.env`
      not clobbered.
- [ ] Systemd unit rendering: render `.service.template` files with sample
      `WORKING_DIRECTORY`/`UV_BIN`, verify output is valid systemd unit syntax.
- [ ] Bootstrap idempotency: run `bootstrap_bare.py` twice against a test
      mongo. Second run prints "already exists", upserts ds1 without error.
- [ ] `install.py --help` parses without import errors (proves vendoring correct).

## Integration (needs Ubuntu 26.04 host)

- [ ] `apt-get install valkey-server rabbitmq-server` works from 26.04
      main/universe. Confirm Valkey is the actual package (not a transitional).
- [ ] Valkey conf.d: verify `/etc/valkey/valkey.conf` supports `include`
      directives and the drop-in pattern. If Valkey uses a different config
      layout, adjust.
- [ ] RabbitMQ 4.0 config keys: verify `listeners.tcp.local`,
      `management.tcp.ip`, `web_stomp.tcp.listener`, and auth-backend-http
      keys parse correctly under 4.0.5 (some changed between 3.x and 4.x).
- [ ] RabbitMQ plugins: `rabbitmq_web_stomp`, `rabbitmq_auth_backend_http`,
      `rabbitmq_auth_backend_cache` all ship with the 26.04 package.
- [ ] `systemctl --user` units install and start. `bd-replica` starts,
      `bd-central` waits via `BindsTo=`, `bd-data` waits for central.
      `loginctl enable-linger` persists across logout.
- [ ] Full `install.py` run on clean 26.04. Run twice (idempotency). Verify
      BD serves `/auth/login` on 8081, socket on 8082, XML-RPC on 8080.
- [ ] `sudo host.py enable deploy/nginx/buildingdepot.conf --domain <d> --cert tailscale`
      works. HTTPS on 81/82/15675.

## System-level (BD + other services)

- [ ] Manifest flow: set `$SITE_ENV` to a real `site.env`, run install.py,
      verify `RABBIT_END_PWD` flows from manifest into BD's `.env` and into
      the RabbitMQ user.
- [ ] RabbitMQ token auth: connect with a BD OAuth token as STOMP password,
      verify HTTP backend calls CS at `127.0.0.1:8081/rabbitmq/user`.
- [ ] Web-STOMP end-to-end: publish a reading via DataService, subscribe over
      wss:15675, verify delivery through nginx.
- [ ] `bootstrap_host.py` co-located deploy with BD + backend + UI.
