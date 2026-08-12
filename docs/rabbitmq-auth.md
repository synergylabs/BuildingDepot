# RabbitMQ access control: BD token as the broker credential

## The problem

Dashboards and services consume BuildingDepot's live sensor fan-out from RabbitMQ. The old approach shipped one shared broker username and password to every client, including the browser, where any visitor could read it from the page. A read-only role would shrink the blast radius but a shared static secret in the browser is still wrong, and it puts authorization in the broker's user list rather than in BD, which is the real authority over who may see which sensor.

We also cannot solve this with a stateful proxy on the UI server, and we do not want to mint a second family of tokens. The UI already holds a BD token that grants the user everything they own. The right design is to let that same token authenticate to RabbitMQ, with BD deciding access. One token, one authority, one point of access.

## The decision

RabbitMQ authenticates clients with a BD OAuth token instead of a broker password, and delegates every authorization decision to BD. A client connects with its email as the login and its BD token as the passcode. RabbitMQ asks CentralService to validate the token and to authorize each resource and each sensor. BD answers from the same ACL it already uses for its HTTP API.

This uses RabbitMQ's first-party `rabbitmq_auth_backend_http` plugin, with `rabbitmq_auth_backend_cache` in front so BD is not called on every operation.

### Why not JWT / oauth2

The oauth2 backend validates signed JWTs locally. BD tokens are opaque random strings stored in Mongo and cached in Redis, not JWTs (`check_oauth` in `CentralService/app/rest_api/helper.py`). So the broker cannot verify them on its own, it has to ask BD. The HTTP backend is exactly that delegation, and it reuses the BD token as-is with no reformatting.

### Additive, not destructive

The backends run as an ordered chain: `internal` then the cached HTTP backend. RabbitMQ tries them in order, and the first backend that authenticates a user also authorizes it. So `bdadmin` (broker ops and the ingest publisher) authenticates against the internal backend and never reaches BD, exactly as before. Only token-bearing consumers fall through to the HTTP backend. Enabling this changes nothing about existing internal users, and removing it from the chain reverts cleanly.

## How it works

RabbitMQ POSTs to four CentralService endpoints under `/rabbitmq`, each returning the literal text `allow` or `deny`.

- **user** receives the email (username) and the BD token (password). It resolves the token to its owner and allows only when the owner matches the supplied username, which binds the connection's identity to the real token owner so later checks can trust the username.
- **vhost** allows the single `/` vhost.
- **resource** lets a consumer read the `master_exchange` and fully manage its own transient subscription queues. Publishing and declaring the exchange are left to the internal user, so everything else is denied.
- **topic** is the per-sensor gate. RabbitMQ calls it with the routing key, which is the `sensor_id`, which is the `Sensor.name` in BD. It allows a read only when BD's ACL grants this user read on that sensor.

Two pieces of BD logic are reused rather than reimplemented: `user_for_token` (the Redis-then-Mongo token resolver, factored out of `check_oauth` so validation lives in one place) and `permission(sensor, email)` (the full per-sensor ACL, covering ownership, dataservice admins, and shared sensor and user groups).

### Topic exchange

Per-sensor authorization only works if `master_exchange` is a `topic` exchange, because RabbitMQ runs its per-routing-key authorization callback only for topic exchanges. The publisher now declares it `topic`. Exact `sensor_id` keys carry no wildcards, so they match identically to the previous `direct` behavior, and subscribers are unaffected.

### The dependency it adds

RabbitMQ now needs `bd-central` reachable to authorize new connections and uncached topic checks. The cache softens this, and BD is already a hard dependency for the whole stack, so this is acceptable. Internal users still work if BD is down.

## Implementation

New code is contained in one place: a single blueprint, `CentralService/app/rabbitmq_auth/__init__.py`, holding the four endpoints. Everything else is small, surgical edits.

| Change | File |
|---|---|
| The four auth endpoints | `CentralService/app/rabbitmq_auth/__init__.py` (new) |
| Register the blueprint at `/rabbitmq` | `CentralService/app/__init__.py` |
| Factor `user_for_token` out of `check_oauth` for reuse | `CentralService/app/rest_api/helper.py` |
| Publish to a `topic` exchange | `DataService/app/rest_api/helper.py` |
| Enable the two auth plugins | `docker/rabbitmq-enabled-plugins` |
| Backend chain, cache, and the four endpoint URLs | `docker/rabbitmq.conf` |

The endpoints are unauthenticated at the Flask layer because RabbitMQ calls them and they validate the passed token themselves. They are reached internally at `http://bd-central:8081/rabbitmq/*`, never through nginx, so in production they should stay on the internal network.

### Verification

Tested by connecting with a real BD token and attempting to bind a queue to `master_exchange`:

- read a sensor the user owns: allowed
- read a routing key the user does not own: denied at the topic check
- a bad token: connection refused at the user check
- a valid token but a mismatched username: refused, so a token cannot be replayed under another identity
- `bdadmin` over the internal backend: unaffected

CentralService logged the matching `/rabbitmq/user`, `/vhost`, `/resource`, and `/topic` callbacks, confirming RabbitMQ delegated each decision to BD.

## Future: variable-TTL tokens for background work

Not implemented, captured here so the design accounts for it. Today a consumer's access is only as durable as the user's token. Background work — for example a long-running analytics or aggregation job — needs to keep a live subscription running after the user has gone away. The plan is for the control plane to mint tokens with a longer, bounded TTL scoped to the relevant sensors, so a background job can hold a valid subscription without a human present, while interactive sessions keep using the user's normal short-lived token. Nothing in the current backend has to change to support this: the same `user_for_token` plus `permission` path authorizes whatever token is presented. The work is in issuing and scoping those tokens, which belongs to the next phase.
