# Bare-metal deploy — testing checklist

## Unit-level (no target host needed)

- [ ] Config loading: import `buildingdepot/bd_config.py` with a complete `.env`
      and verify every key in `CONFIG`. Then blank `REDIS_PWD` and verify the
      import raises naming the key and the file. Then set `REDIS_PWD` in the
      process environment and verify it wins over the file.
- [ ] `BD_ENV` override: point it at a scratch env file, verify `bd_config`
      reads that instead of the repo-root `.env`.
- [ ] Config reachability from each working directory: the units run from
      `buildingdepot/` (CS, DS) and `buildingdepot/CentralReplica/` (replica).
      Verify `import bd_config` resolves from both, and that the replica's
      `sys.path` bootstrap in `main.py` is what makes the second one work.
- [ ] Env provisioning: run `manifest.apply_site_env()` with and without a
      manifest. Verify secrets generated, manifest keys mapped, existing `.env`
      not clobbered.
- [ ] Key-name parity: every `_required`/`_text`/`_number` key in `bd_config.py`
      appears in `.env.example`, and every `${...}` in `deploy/compose.yml`
      resolves from `.env`.
- [ ] Systemd unit rendering: render `.service.template` files with sample
      `WORKING_DIRECTORY`/`UV_BIN`, verify output is valid systemd unit syntax.
- [ ] Bootstrap idempotency: run `bootstrap_bare.py` twice against a test
      mongo. Second run prints "already exists", upserts ds1 without error.
- [ ] OAuth client registration: run `bootstrap_bare.py` with
      `--client-id`/`--client-secret`, verify the row lands in the **`client`**
      collection (not a `Database.client` attribute), then authenticate with
      `GET /oauth/access_token/client_id=.../client_secret=...` and check a token
      comes back. Re-run with a changed secret and verify the row updates rather
      than duplicating. Omit both flags and verify it skips cleanly.
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

- [ ] Unified env flow: symlink the shared `site.env` to each app's `.env`, run
      the installers in order, and verify the shared RabbitMQ credentials reach BD
      and the UI.
- [ ] RabbitMQ token auth: connect with a BD OAuth token as STOMP password,
      verify HTTP backend calls CS at `127.0.0.1:8081/rabbitmq/user`.
- [ ] Web-STOMP end-to-end: publish a reading via DataService, subscribe over
      wss:15675, verify delivery through nginx.
- [ ] Co-located deploy with BD + backend + UI, including required Broker
      enrollment and host nginx/TLS setup.
