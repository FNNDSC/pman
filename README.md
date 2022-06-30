# ![ChRIS logo](https://github.com/FNNDSC/ChRIS_ultron_backEnd/blob/master/docs/assets/logo_chris.png) pman

[![Version](https://img.shields.io/docker/v/fnndsc/pman?sort=semver)](https://hub.docker.com/r/fnndsc/pman)
[![MIT License](https://img.shields.io/github/license/fnndsc/pman)](LICENSE)
[![ci](https://github.com/FNNDSC/pman/actions/workflows/ci.yml/badge.svg)](https://github.com/FNNDSC/pman/actions/workflows/ci.yml)

_pman_, which once stood for **p**rocess **man**ager,
is a [Flask](https://flask-restful.readthedocs.io/) application
providing an API for creating jobs with various schedulers e.g.
Kubernetes, Docker Swarm, and SLURM.
It basically translates its own JSON interface to requests for
the various supported backends.

_pman_ is tightly-coupled to
[_pfcon_](https://github.com/FNNDSC/pfcon). _pman_ and _pfcon_
are typially deployed as a pair, providing the _pfcon_ service.

## Development

This section describes how to set up a local instance of *pman* working against swarm.

### Using Docker Compose

The easiest way to run a code hot-reloading server for
development is using docker-compose.

```shell
docker swarm init --advertise-addr 127.0.0.1
docker compose up -d
```

### Using Docker Swarm

To run a full test using `docker stack deploy`,
run the test harness `test_swarm.sh`.

```shell
./test_swarm.sh
```

## Configuration

_pman_ is configured by environment variables.
Refer to the source code in [pman/config.py](pman/config.py)
for exactly how it works.

| Environment Variable | Description                                          |
|----------------------|------------------------------------------------------|
| `CONTAINER_ENV`      | one of: "swarm", "kubernetes", "cromwell"            |
| `STORAGE_TYPE`       | one of: "host", "nfs"                                |
| `STOREBASE`          | where job data is stored, [see below](#STOREBASE)    |
| `NFS_SERVER`         | NFS server address, required when `STORAGE_TYPE=nfs` |
| `JOB_LOGS_TAIL`      | (int) maximum size of job logs                       |

### `STOREBASE`

- If `STORAGE_TYPE=host`, then `STOREBASE` represents the path on the
container host.
- If `STORAGE_TYPE=nfs`, then `STOREBASE` should be an exported NFS share

### Kubernetes-Specific Options

Applicable when `CONTAINER_ENV=kubernetes`

| Environment Variable           | Description                                     |
|--------------------------------|-------------------------------------------------|
| `JOB_NAMESPACE`                | Kubernetes namespace for created jobs           |
| `SECURITYCONTEXT_RUN_AS_USER`  | Job container UID (NFS permissions workaround)  |
| `SECURITYCONTEXT_RUN_AS_GROUP` | Job container GID  (NFS permissions workaround) |

### SLURM-Specific Options

Applicable when `CONTAINER_ENV=cromwell`

| Environment Variable | Description                                          |
|----------------------|------------------------------------------------------|
| `CROMWELL_URL`       | Cromwell URL                                         |
| `TIMELIMIT_MINUTES`  | SLURM job time limit                                 |

For how it works, see https://github.com/FNNDSC/pman/wiki/Cromwell

## Limitations

The system administrator is expected to have an existing solution for having
a "shared volume" visible on the same path to every node in the cluster
(which is typically how NFS is used). The path on each host to this share
should be provided as the value for `STOREBASE`.

Currently, only HostPath and NFS volumes are supported.
_pfcon_ and _pman_ do not support (using nor creating) other kinds of PVCs.

## TODO

- [ ] Example for how to interact with _pman_ directly (w/o _pfcon_)
- [ ] Dev environment and testing for Kubernetes and SLURM.
