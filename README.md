# ![ChRIS logo](https://github.com/FNNDSC/ChRIS_ultron_backEnd/blob/master/docs/assets/logo_chris.png) pman

[![Version](https://img.shields.io/docker/v/fnndsc/pman?sort=semver)](https://hub.docker.com/r/fnndsc/pman)
[![MIT License](https://img.shields.io/github/license/fnndsc/pman)](LICENSE)
[![ci](https://github.com/FNNDSC/pman/actions/workflows/ci.yml/badge.svg)](https://github.com/FNNDSC/pman/actions/workflows/ci.yml)

> [!CAUTION]
> _pman_ has been deprecated and integrated into [_pfcon_](https://github.com/FNNDSC/pfcon).

_pman_, which once stood for **p**rocess **man**ager,
is a [Flask](https://flask-restful.readthedocs.io/) application
providing an API for creating jobs with various schedulers e.g.
Kubernetes, Podman, Docker Swarm, and SLURM.
It basically translates its own JSON interface to requests for
the various supported backends.

_pman_ is tightly-coupled to
[_pfcon_](https://github.com/FNNDSC/pfcon). _pman_ and _pfcon_
are typically deployed as a pair, providing the _pfcon_ service.

## Running `pman`

The easiest way to see it in action is to run
[_miniChRIS-docker_](https://github.com/FNNDSC/miniChRIS-docker).
The instructions that follow are for _pman_ hackers and developers.

## Development

This section describes how to set up a local instance of *pman* for development.

### Using Docker Compose

These instructions run _pman_ inside a container using Docker and Docker Swarm for scheduling jobs.
Hot-reloading of changes to the code is enabled.

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

### Using Podman for Development

_pman_ must be able to schedule containers via Podman by communicating to the Podman socket.

```shell
systemctl --user start podman.service
export DOCKER_HOST="$(podman info --format '{{ .Host.RemoteSocket.Path }}')"
```

#### Install _pman_ using Python

```shell
python -m venv venv
source venv/bin/activate
pip install -r requirements/local.txt
pip install -e .
```

#### Run _pman_ using Python in Development Mode

```shell
python -m pman
```

### Using Kubernetes via Kind

https://github.com/FNNDSC/pman/wiki/Development-Environment:-Kubernetes

## Configuration

_pman_ is configured by environment variables.
Refer to the source code in [pman/config.py](pman/config.py)
for exactly how it works.

### How Storage Works

_pman_ relies on _pfcon_ to manage data in a directory known as "storeBase."
The "storeBase" is a storage space visible to every node in your cluster.

For single-machine deployments using Docker and Podman, the best solution
is to use a local volume mounted by _pfcon_ at `/var/local/storeBase`.
_pman_ should be configured with `STORAGE_TYPE=docker_local_volume` `VOLUME_NAME=...`.

On Kubernetes, a single PersistentVolumeClaim should be used. It is mounted
by _pfcon_ at `/var/local/storeBase`.
_pman_ should be configured with `STORAGE_TYPE=kubernetes_pvc` `VOLUME_NAME=...`.

SLURM has no concept of volumes, though SLURM clusters typically use a NFS share
mounted to the same path on every node. _pman_ should be configured with
`STORAGE_TYPE=host` `STOREBASE=...`, specify the share mount point as `STOREBASE`.

#### `swarm` v.s. `docker`

Originally, _pman_ interfaced with the Docker Swarm API for the sake of supporting multi-node clusters.
However, more often than not, _pman_ is run on a single-machine. Such is the case for developer
environments, "host" compute resources for our single-machine production deployments of CUBE,
and production deployments of _CUBE_ on our Power9 supercomputers. Swarm mode is mostly an annoyance
and its multi-node ability is poorly tested. Furthermore, multi-node functionality is
better provided by `CONTAINER_ENV=kubernetes`.

In _pman_ v4.1, `CONTAINER_ENV=docker` was introduced as a new feature and the default configuration.
In this mode, _pman_ uses the Docker Engine API instead of the Swarm API, which is much more convenient
for single-machine use cases.

### Podman Support

**`CONTAINER_ENV=docker` is compatible with Podman.**

Podman version 3 or 4 are known to work.

#### Rootless Podman

Configure the user to be able to set resource limits.

https://github.com/containers/podman/blob/main/troubleshooting.md#symptom-23

### Environment Variables

| Environment Variable     | Description                                                                                                                     |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| `SECRET_KEY`             | [Flask secret key][flask docs]                                                                                                  |
| `CONTAINER_ENV`          | one of: "swarm", "kubernetes", "cromwell", "docker"                                                                             |
| `STORAGE_TYPE`           | one of: "host", "docker_local_volume", "kubernetes_pvc"                                                                         |
| `STOREBASE`              | where job data is stored, valid when `STORAGE_TYPE=host`, conflicts with `VOLUME_NAME`                                          |
| `VOLUME_NAME`            | name of data volume, valid when `STORAGE_TYPE=docker_local_volume` or `STORAGE_TYPE=kubernetes_pvc`                             |
| `PFCON_SELECTOR`         | label on the pfcon container, may be specified for pman to self-discover `VOLUME_NAME` (default: `org.chrisproject.role=pfcon`) |
| `CONTAINER_USER`         | Set job container user in the form `UID:GID`, may be a range for random values                                                  | 
| `ENABLE_HOME_WORKAROUND` | If set to "yes" then set job environment variable `HOME=/tmp`                                                                   |
| `SHM_SIZE`               | Size of `/dev/shm` in mebibytes. (Supported only in Docker, Podman, and Kubernetes.)                                            |
| `JOB_LABELS`             | CSV list of key=value pairs, labels to apply to container jobs                                                                  |
| `JOB_LOGS_TAIL`          | (int) maximum size of job logs                                                                                                  |
| `IGNORE_LIMITS`          | If set to "yes" then do not set resource limits on container jobs (for making things work without effort)                       |
| `REMOVE_JOBS`            | If set to "no" then pman will not delete jobs (for debugging)                                                                   |

[flask docs]: https://flask.palletsprojects.com/en/2.1.x/config/#SECRET_KEY

### `STOREAGE_TYPE=host`

When `STORAGE_TYPE=host`, then specify `STOREBASE` as a mount point path on the host(s).

### `STOREAGE_TYPE=docker_local_volume`

For single-machine instances, use a Docker/Podman local volume as the "storeBase."
The volume should exist prior to the start of _pman_. It can be identified one of
two ways:

- Manually, by passing the volume name to the variable `VOLUME_NAME`
- Automatically: _pman_ inspects a container with the label `org.chrisproject.role=pfcon`
  and selects the mountpoint of the bind to `/var/local/storeBase`

#### `STORAGE_TYPE=kubernetes_pvc`

When `STORAGE_TYPE=kubernetes_pvc`, then `VOLUME_NAME` must be the name of a
PersistentVolumeClaim configured as ReadWriteMany.

In cases where the volume is only writable to a specific UNIX user,
such as a NFS-backed volume, `CONTAINER_USER` can be used as a workaround.

### Kubernetes-Specific Options

Applicable when `CONTAINER_ENV=kubernetes`

| Environment Variable      | Description                                     |
|---------------------------|-------------------------------------------------|
| `JOB_NAMESPACE`           | Kubernetes namespace for created jobs           |
| `NODE_SELECTOR`           | Pod `nodeSelector`                              |

### SLURM-Specific Options

Applicable when `CONTAINER_ENV=cromwell`

| Environment Variable | Description                                          |
|----------------------|------------------------------------------------------|
| `CROMWELL_URL`       | Cromwell URL                                         |
| `TIMELIMIT_MINUTES`  | SLURM job time limit                                 |

For how it works, see https://github.com/FNNDSC/pman/wiki/Cromwell

### Container User Security

Setting an arbitrary container user, e.g. with `CONTAINER_USER=123456:123456`,
increases security but will cause (unsafely written) _ChRIS_ plugins to fail.
In some cases, `ENABLE_HOME_WORKAROUND=yes` can get the plugin to work
without having to change its code.

It is possible to use a random container user with `CONTAINER_USER=1000000000-2147483647:1000000000-2147483647`
however considering that *pfcon*'s UID never changes, this will cause everything to break.

## Missing Features

_pman_'s configuration has gotten messy over the years because it attempts to provide an interface
across vastly different systems. Some mixing-and-matching of options are unsupported:

- `IGNORE_LIMITS=yes` only works with `CONTAINER_ENV=docker` (or podman).
- `JOB_LABELS=...` only works with `CONTAINER_ENV=docker` (or podman) and `CONTAINER_ENV=kubernetes`.
- `CONTAINER_USER` does not work with `CONTAINER_ENV=cromwell`
- `CONTAINER_ENV=cromwell` does not forward environment variables.
- `STORAGE_TYPE=host` is not supported for Kubernetes

## TODO

- [ ] Dev environment and testing for Kubernetes and SLURM.
