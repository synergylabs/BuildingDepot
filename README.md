BuildingDepot v3.3 ([link](https://buildingdepot.org/))
====================

![BuildingDepot](https://github.com/synergylabs/BuildingDepot-v3/workflows/BuildingDepot/badge.svg)

BuildingDepot (BD) is a data storage and actuation system for building
management and control. A central server exposes a RESTful API to send (POST)
and retrieve (GET) data — typically sensor time series from buildings (wireless
sensor networks, existing SCADA systems, and related sources). BD is made up of
three services: the **CentralService**, the **DataService**, and the
**CentralReplica**.

Quick start (Docker)
====================

The default deployment is Docker Compose (Mongo, Redis, InfluxDB 1.8, RabbitMQ,
and the three BD processes), with a **host nginx** terminating TLS in front. The
app ports are published to host loopback only.

```shell
git clone <repo-url> && cd BuildingDepot
python3 deploy/install.py        # provision docker/.env, build + up, bootstrap admin/ds1/client
```

`deploy/install.py` provisions `deploy/docker/.env`, builds and starts the
stack, and registers the admin user (`admin@buildingdepot.org`, temp password
printed) and the `ds1` data service. Then put HTTPS in front (root, once per
host):

```shell
sudo python3 deploy/shared/host.py install
sudo python3 deploy/shared/host.py enable deploy/nginx/buildingdepot.conf.sample \
    --domain <host> --cert <tailscale|letsencrypt>
```

Reach CentralService at `https://<host>:81` and DataService at `https://<host>:82`.

Documentation
=============

| Read this | For |
|---|---|
| [`docs/deployment.md`](docs/deployment.md) | full deploy: install, host nginx, cert modes |
| [`deploy/docker/README.md`](deploy/docker/README.md) | the compose stack: email, RabbitMQ token auth, Podman |
| [`docs/docker-implementation.md`](docs/docker-implementation.md) | how the Docker packaging works internally |

Layout
======

```
BuildingDepot/
├── deploy/
│   ├── install.py                     # docker provision + build + bootstrap
│   ├── shared/                        # vendored deploy library (do not edit)
│   ├── docker/                        # compose stack, Dockerfile, entrypoint, bootstrap
│   └── nginx/buildingdepot.conf.sample  # host nginx site fragment (81/82/15675)
├── docs/                             # deployment + docker internals
├── buildingdepot/                    # BD source (CentralService, DataService, CentralReplica)
├── scripts/                          # repo/dev utilities
├── install.sh, env.sample, setup_bd.py  # legacy baremetal installer
└── configs/, pip_packages.list, Dockerfile, script_for_github_actions.sh  # baremetal + CI
```

The legacy baremetal installer (`install.sh`, `setup_bd.py`, `env.sample`,
`configs/`) stays at the repo root, alongside the top-level `Dockerfile` +
`script_for_github_actions.sh` used by the baremetal CI
(`.github/workflows/test_bd.yml`).

License
=======

See [`license.txt`](license.txt).
