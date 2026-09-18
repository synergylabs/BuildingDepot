BuildingDepot v3.3 ([link](https://buildingdepot.org/))
====================

![BuildingDepot](https://github.com/synergylabs/BuildingDepot-v3/workflows/BuildingDepot/badge.svg)

BuildingDepot (BD) is a data storage and actuation system for building
management and control. A central server exposes a RESTful API to send (POST)
and retrieve (GET) data — typically sensor time series from buildings (wireless
sensor networks, existing SCADA systems, and related sources). BD is made up of
three services: the **CentralService**, the **DataService**, and the
**CentralReplica**.

Quick start
===========

BD runs **bare metal** under systemd user units (the three Python services,
Valkey, RabbitMQ), with only the two datastores that cannot come from apt —
MongoDB 7 and InfluxDB 1.8 — in loopback-only containers. A **host nginx**
terminates TLS in front.

```shell
git clone <repo-url> && cd BuildingDepot
python3 deploy/install.py        # provision .env, install services, bootstrap admin/ds1
```

`deploy/install.py` provisions the repo-root `.env`, installs the apt packages
and systemd units, brings up the datastore containers, and registers the admin
user (`admin@buildingdepot.org`, temp password printed) and the `ds1` data
service. Accepts `--no-ask-sudo` to suppress sudo confirmation prompts (used by
`bootstrap_host.py` for unattended installs). Then put HTTPS in front (root,
once per host):

```shell
sudo python3 deploy/shared/host.py install
sudo python3 deploy/shared/host.py enable deploy/nginx/buildingdepot.conf \
    --domain <host> --cert <tailscale|http|dns-cloudflare>
```

Reach CentralService at `https://<host>:81` and DataService at `https://<host>:82`.

Configuration
=============

One file: `.env` at the repo root, gitignored, chmod 600. Its keys are the Flask
config keys verbatim, and `buildingdepot/bd_config.py` reads it directly — there
is no generated settings file. Copy `.env.example` to start by hand, or let
`deploy/install.py` provision it with fresh secrets. Structural values (database
names, `NAME=ds1`, default hosts and ports) are defaults in `bd_config.py`, not
env keys.

For a multi-service deployment, follow the authoritative procedure in
[`Mites-Deploy/README.md`](../Mites-Deploy/README.md).
This installer provisions BuildingDepot only; host nginx, TLS, firewall rules, and
user-service linger are separate host steps.

Documentation
=============

| Read this | For |
|---|---|
| [`docs/deployment.md`](docs/deployment.md) | full deploy: install, host nginx, cert modes, email, RabbitMQ token auth |
| [`docs/architecture.md`](docs/architecture.md) | what BD is, what each process does, how the pieces find each other |

Layout
======

```
BuildingDepot/
├── .env.example                   # the only config surface (copy to .env)
├── deploy/
│   ├── install.py                 # provision .env + packages + services + bootstrap
│   ├── bootstrap_bare.py          # admin user + ds1 registration
│   ├── compose.yml                # Mongo + Influx (+ mailpit in --dev), loopback only
│   ├── systemd/                   # bd-replica, bd-central, bd-data user units
│   ├── rabbitmq/                  # broker config + enabled plugins
│   ├── shared/                    # vendored deploy library (do not edit)
│   └── nginx/buildingdepot.conf   # host nginx site fragment (81/82/15675)
├── docs/                          # deployment + architecture
├── buildingdepot/                 # BD source
│   ├── bd_config.py               # reads .env; the single config module
│   ├── CentralService/            # REST API + auth (gunicorn, 8081)
│   ├── DataService/               # timeseries read/write (gunicorn, 8082)
│   └── CentralReplica/            # shared XML-RPC authority (8080)
├── legacy_scripts/                # superseded baremetal installer
└── configs/, pip_packages.list, Dockerfile, script_for_github_actions.sh, setup_bd.py, env.sample
```

The legacy baremetal installer (`legacy_scripts/install.sh`, `setup_bd.py`,
`env.sample`, `configs/`) and the baremetal CI (`script_for_github_actions.sh`,
`.github/workflows/test_bd.yml`) predate the current deploy path and **no longer
work** — see the TODO at the top of the workflow.

Do not run `legacy_scripts/install.sh` on a configured host: its line
`cp env.sample .env` overwrites the real `.env` with the two stale `BD_SETTINGS`
paths, taking every secret with it.

License
=======

See [`license.txt`](license.txt).
