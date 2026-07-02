# BuildingDepot on Docker: how this stack is built and why

This is the guide for someone who has never touched BuildingDepot and now has to run it, understand it, or change it. It explains what BuildingDepot is, what each container does, why the setup is split the way it is, and how to bring it all up from nothing. Read it top to bottom once and the compose file will stop looking mysterious.

## What BuildingDepot is

BuildingDepot (BD) is a store for building sensor data. It keeps two very different kinds of data and keeps them separate on purpose. The first is the data model: buildings, the sensors in them, the tags that describe those sensors, the users who can see them, and the access rules. The second is the actual timeseries: the stream of readings each sensor produces over time. BD is the sink: an upstream backend writes sensor samples into BD, which is where downstream services such as dashboards and analytics later read them from.

BD is an old codebase. It was written to run as a few Python processes sitting on one machine next to their databases, talking to each other over localhost. This compose stack takes that same code and runs each piece in its own container, which is cleaner and reproducible, but it means a few places where the code assumed localhost have to be nudged to point at the right container instead. Those nudges are called out below so they do not surprise you.

## The shape of the stack

There are eight containers. Four are off-the-shelf data stores, three are BuildingDepot's own processes, and one is a dev mail catcher. TLS termination is **not** in this stack — a host nginx (outside compose) fronts it; see [`../docs/deployment.md`](deployment.md). They split into three groups.

The backing stores hold state:

- **mongo** is the metadata database. Users, buildings, sensors, tags, OAuth clients, and the registry of data services all live here. This is BD's source of truth for everything except the raw timeseries.
- **influxdb** is the timeseries database, where the sensor readings themselves go. It is pinned to the 1.8 line because BD's Python client speaks the InfluxDB v1 protocol. Do not bump it to 2.x without porting that client.
- **redis** holds short-lived state: OAuth access tokens, and the temporary passwords from the reset flow that expire after fifteen minutes.
- **rabbitmq** is the live fan-out. When sensor data lands, BD publishes it to a RabbitMQ exchange, and anything that wants the live stream subscribes. Native clients use AMQP, and browsers use web-STOMP over a websocket. This is the only data store whose ports are published to the host, because those live consumers run outside the compose network.

The three BuildingDepot processes are where BD's own logic runs:

- **bd-replica** is the CentralReplica. It is a small XML-RPC server on port 8080 that the other two processes call for shared central operations. Think of it as the inner authority the API layer leans on.
- **bd-central** is the CentralService, usually shortened to CS. This is the main REST API. Login and OAuth, creating users, defining buildings and sensors, tags, permissions: all of it is CS. It runs under gunicorn on 8081.
- **bd-data** is the DataService, shortened to DS. This is the timeseries side. Posting readings and querying them back out of InfluxDB goes through DS. It runs under gunicorn on 8082, with a longer request timeout because timeseries queries can be heavy.

The gunicorn ports are published to **host loopback** — CS on `127.0.0.1:8081`, DS on `127.0.0.1:8082` — and RabbitMQ's plain web-STOMP on `127.0.0.1:15674`. Nothing binds a public interface here. A **host nginx**, outside this stack, terminates TLS on 81/82 (and wss on 15675) and forwards to those loopback ports. Keeping TLS on the host lets one nginx front BD alongside other co-located services and keeps the private key out of every container.

Last is **mailpit**, which only exists in dev. CentralService emails a temporary password on signup and password reset, and with no real mail server around, mailpit catches those messages so you can read them in a browser. It is described in the README, not here.

## One image, three different processes

All three BD processes are the same code, so they are the same image. `Dockerfile.bd` builds one `buildingdepot:dev` image: a slim Python 3.12 base, dependencies installed with uv from the locked pyproject, then the `buildingdepot` source copied in. The image does not pick a process to run. That choice is made in compose.

The compose file uses a YAML anchor called `x-bd-app` to avoid repeating itself. The anchor carries the build instructions, the env file, the restart policy, and the dependency on the four data stores. Each of the three BD services pulls in that anchor and then sets its own `command:`. The replica runs `python3 main.py`, central runs gunicorn against `CentralService:app`, and data runs gunicorn against `DataService:app`. Same image, three jobs, decided by the command line.

## How configuration and secrets work

BD reads its settings from a file, not from environment variables directly. CS and DS load a Flask config file whose path is given by the `BD_SETTINGS` environment variable, and CentralReplica imports a plain `config.py` module. Rather than baking either file into the image, the image's entrypoint writes both of them at container start from environment values. That keeps every secret out of the built image and lets the same image run against different credentials.

So the flow on each container boot is: `entrypoint.sh` reads the environment, checks the required secrets are present, renders `bd_settings.cfg` and `CentralReplica/config.py`, and then execs the service command. The environment values themselves come from `docker/.env`, which compose loads through the anchor. This is why `.env` is the one file you must fill in before anything works, and why it is git-ignored.

The entrypoint does one more thing worth knowing. The legacy CS and DS code hardcodes the CentralReplica's address as localhost, because originally the replica ran on the same machine. In this stack the replica is its own container named bd-replica, so the entrypoint runs two small sed patches that rewrite those localhost XML-RPC URLs to `bd-replica:8080`. Without that the API processes could not reach the replica.

## How the pieces find each other

Containers on the same compose network reach each other by service name. CS and DS connect to `mongo`, `redis`, `influxdb`, and `rabbitmq` by those names, which is exactly what the rendered settings contain. The replica is reached at `bd-replica`. The host nginx, being outside the network, reaches CS and DS through their published loopback ports, not by service name.

There is one registration detail that lives in the database rather than in config. BD keeps a registry of data services in Mongo, and CS looks a data service up there to find the host it should call for certain operations. The bootstrap step writes a row named `ds1` with its host set to `bd-replica`, so that CS's lookups resolve to the replica container. That row is easy to miss and the system does not work without it, which is why bootstrap creates it for you.

## Bringing it up from zero

You need Docker with the compose plugin. Everything below runs from this `docker/` directory.

First, create your environment file and fill in secrets:

```bash
cp .env.example .env
```

Open `.env` and replace every `replace-me`. The header of the file has a one-liner that generates strong values with openssl. These are the Mongo, Influx, Redis, and RabbitMQ credentials plus the Flask secret key. The same values get rendered into the BD settings at boot, so the apps and the stores agree.

Then build the image and start the whole stack:

```bash
docker compose up -d --build
```

Compose builds `buildingdepot:dev` once, starts the four data stores, waits for each to report healthy, then starts the replica, then CS and DS once the replica is healthy. The health gating is why startup is ordered and not a race.

Now create the admin user and register the data service:

```bash
./bootstrap_admin.sh
```

This runs a short script inside the bd-central container. It inserts the super user `admin@buildingdepot.org` into Mongo with a random temporary password that it prints once, and it upserts the `ds1` data service row pointing at bd-replica. Running it again is safe. If the admin already exists, Mongo rejects the duplicate and the script moves on.

At this point BD is up with an empty data model. Populate it (tag types, buildings, sensors, users) by calling CS's REST API with admin OAuth client credentials.

To check the stack is serving:

```bash
curl -s -o /dev/null -w "CS %{http_code}\n" http://127.0.0.1:8081/auth/login
curl -s -o /dev/null -w "DS %{http_code}\n" http://127.0.0.1:8082/
```

(These hit the loopback app ports directly. Public HTTPS on 81/82 is the host
nginx's job — see [`deployment.md`](deployment.md).)

## Ports and who talks to them

| Host binding | Lands on | Used by |
|---|---|---|
| 127.0.0.1:8081 | CentralService (gunicorn) | host nginx -> REST API: login, users, buildings, sensors, tags |
| 127.0.0.1:8082 | DataService (gunicorn) | host nginx -> timeseries reads and writes |
| 127.0.0.1:15674 | RabbitMQ web-STOMP (plain ws) | host nginx -> browser live streaming (wss on 15675) |
| 5672 | RabbitMQ AMQP | native live consumers |
| 15672 | RabbitMQ management | the broker's admin UI and HTTP API |
| 8025 | mailpit | reading dev signup and reset emails |

CS/DS/web-STOMP are published to **loopback only**; the host nginx terminates
TLS on 81/82/15675 and proxies to them. The replica's 8080 and the four data
stores' own ports stay inside the compose network. AMQP (5672) and the
management UI (15672) are published on all interfaces for native clients and
ops.

## Day to day

Logs come from compose. `docker compose logs -f bd-central` follows CentralService, and the same works for any service name. The CS access log is noisy because the health check hits `/auth/login` every few seconds, so filter that out when you are hunting for real errors.

After a code change, rebuild and restart with `docker compose up -d --build`. Compose rebuilds the shared image and recreates the BD services that use it.

Because the host nginx proxies to fixed loopback ports (`127.0.0.1:8081`/`8082`)
rather than to container IPs, recreating a BD app container does not strand
nginx — Docker re-establishes the published port mapping, and nginx keeps
pointing at the same loopback address.

Email is dev-only: mailpit catches signup/reset mail on 8025 (see
[`../deploy/docker/README.md`](../deploy/docker/README.md)). TLS is handled by
the host nginx with a Tailscale or Let's Encrypt cert — see
[`deployment.md`](deployment.md).

## State and resetting

The four data stores keep their data in named volumes: `mongo-data`, `redis-data`, `influx-data`, and `rabbit-data`. They survive `docker compose down` and a normal restart. To wipe everything and start from a truly blank slate, `docker compose down -v` removes the volumes too, after which you start over from the env file and bootstrap.

## Why it is shaped this way

The design choices all come back to a few ideas. Keep the metadata and the timeseries in the databases each is good at, which is Mongo and InfluxDB. Run BD's three processes as separate containers so each can be scaled, restarted, and read in logs on its own, while still sharing one image so there is only one thing to build. Render config and secrets at container start so the image stays clean and portable. Publish the app ports to host loopback and let a single host nginx terminate TLS in front, so there is one address surface and one place for TLS across every co-located service, and no private key ever enters a container. Expose RabbitMQ to the host because the live consumers genuinely live outside this stack. Everything else, the health gating, the bootstrap, the XML-RPC patching, exists to make an older single-host codebase behave correctly now that its parts live in separate containers.
