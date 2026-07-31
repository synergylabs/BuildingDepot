Slop warning: doc is LLM-written and written primarily for LLM consumption.
Humans may read but information may be confusing or poorly-communicated.

# BuildingDepot: what it is and how the pieces fit

This is the guide for someone who has never touched BuildingDepot and now has to
run it, understand it, or change it. It explains what BD is, what each process
does, why the setup is split the way it is, and how the parts find each other.
Read it top to bottom once and the deploy layout will stop looking mysterious.

## What BuildingDepot is

BuildingDepot (BD) is a store for building sensor data. It keeps two very
different kinds of data and keeps them separate on purpose. The first is the data
model: buildings, the sensors in them, the tags that describe those sensors, the
users who can see them, and the access rules. The second is the actual
timeseries: the stream of readings each sensor produces over time. BD is the
sink — an upstream backend writes sensor samples into BD, which is where
downstream services such as dashboards and analytics later read them from.

BD is an old codebase. It was written to run as a few Python processes sitting on
one machine next to their databases, talking to each other over localhost. The
deploy path leans into that rather than fighting it: the processes run bare metal
under systemd, on the same host, reaching each other over loopback.

## The three BD processes

- **bd-replica** is the CentralReplica: a small XML-RPC server on port **8080**
  that the other two processes call for shared central operations. Think of it as
  the inner authority the API layer leans on. It is a plain
  `python3 CentralReplica/main.py`, not a WSGI app.
- **bd-central** is the CentralService, usually shortened to CS. This is the main
  REST API: login and OAuth, creating users, defining buildings and sensors,
  tags, permissions. Under gunicorn on **8081**.
- **bd-data** is the DataService, shortened to DS. This is the timeseries side —
  posting readings and querying them back out of InfluxDB. Under gunicorn on
  **8082**, with a longer request timeout because timeseries queries can be
  heavy.

All three are systemd **user** units (`deploy/systemd/*.service.template`),
chained with `BindsTo=` so central waits for the replica and data waits for
central. They need `loginctl enable-linger` to survive logout.

## The backing stores

- **mongo** is the metadata database — users, buildings, sensors, tags, OAuth
  clients, and the registry of data services. BD's source of truth for
  everything except raw timeseries. Runs as a container (`mongo:7`) published to
  `127.0.0.1:27017`.
- **influxdb** is the timeseries database, where the readings go. Pinned to the
  1.8 line because BD's Python client speaks the InfluxDB v1 protocol. Container,
  `127.0.0.1:8086`.
- **valkey** holds short-lived state: OAuth access tokens, and the temporary
  passwords from the reset flow that expire after fifteen minutes. Bare metal
  from apt, loopback, password + `appendonly yes`.
- **rabbitmq** is the live fan-out. When sensor data lands, BD publishes it to a
  RabbitMQ exchange and anything that wants the live stream subscribes. Native
  clients use AMQP; browsers use web-STOMP over a websocket. Bare metal from apt.

Mongo and Influx are containers only because apt has no usable package for them
at the versions BD needs. Everything else is a native service, which keeps the
process tree, the journal, and the config in one place.

## How configuration works

One file: `.env` at the repo root. `buildingdepot/bd_config.py` parses it,
applies defaults for anything structural, and exposes two things — a `Config`
class (which CentralReplica reads directly) and a `CONFIG` dict (which CS and DS
load into `app.config`). `deploy/compose.yml` reads the same `.env` for the Mongo
and Influx credentials.

Nothing is generated from `.env`. There is no `bd_settings.cfg` and no generated
`CentralReplica/config.py`: earlier versions rendered both from templates at
install time, which meant a secret lived in three places and one of the generated
files was tracked in git. Now the env keys *are* the Flask config keys, so there
is no mapping to keep in sync and no derived artifact to drift.

Because the units run with different working directories, `bd_config.py` locates
`.env` from its own `__file__`, never from the current directory. CentralReplica
runs as a script from its own directory, so `main.py` adds the parent to
`sys.path` before importing `bd_config`.

Required secrets have no default and raise at import. A missing `REDIS_PWD` fails
at service start with a message naming the file and the key, instead of surfacing
as an authentication error from deep inside a driver.

## How the pieces find each other

Everything is on one host, so everything is loopback. CS and DS connect to
`127.0.0.1` for Mongo, Valkey, Influx, and RabbitMQ. Both reach the replica at
`http://127.0.0.1:8080` — that address is hardcoded in the service `__init__.py`
files, which is fine bare metal and was the source of the container-era sed
patching.

One registration detail lives in the database rather than in config. BD keeps a
registry of data services in Mongo, and CS looks a data service up there to find
the host it should call for certain operations. `deploy/bootstrap_bare.py` writes
a row named `ds1` with host `127.0.0.1` and port `8080` — the **replica's**
XML-RPC port, not the DataService's 8082. That row is easy to miss and the system
does not work without it, which is why bootstrap creates it for you.

## Ports

| Binding | Lands on | Used by |
|---|---|---|
| 127.0.0.1:8081 | CentralService (gunicorn) | host nginx -> REST API: login, users, buildings, sensors, tags |
| 127.0.0.1:8082 | DataService (gunicorn) | host nginx -> timeseries reads and writes |
| 127.0.0.1:8080 | CentralReplica (XML-RPC) | CS and DS only |
| 127.0.0.1:15674 | RabbitMQ web-STOMP (plain ws) | host nginx -> browser live streaming (wss on 15675) |
| 127.0.0.1:5672 | RabbitMQ AMQP | native live consumers on this host |
| 127.0.0.1:27017 | MongoDB (container) | all three BD processes |
| 127.0.0.1:8086 | InfluxDB (container) | DataService |
| 127.0.0.1:8025 | mailpit (`--dev` only) | reading dev signup and reset emails |

Nothing binds a public interface. The host nginx terminates TLS on 81, 82, and
15675 and forwards to the loopback ports — see
[`deployment.md`](deployment.md).

## Why it is shaped this way

Keep the metadata and the timeseries in the databases each is good at: Mongo and
InfluxDB. Run BD's three processes as separate systemd units so each can be
restarted and read in the journal on its own, while an older single-host codebase
keeps the localhost assumptions it was written with. Keep configuration in a
single file that is read, not rendered, so there is one place a secret lives.
Bind everything to loopback and let a single host nginx terminate TLS in front,
so there is one address surface and one place for TLS across every co-located
service, and no private key sits next to an application. Containerize only what
apt cannot provide.
