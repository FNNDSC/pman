# ![ChRIS logo](https://github.com/FNNDSC/ChRIS_ultron_backEnd/blob/master/docs/assets/logo_chris.png) pman

[![Version](https://img.shields.io/docker/v/fnndsc/pman?sort=semver)](https://hub.docker.com/r/fnndsc/pman)
[![MIT License](https://img.shields.io/github/license/fnndsc/pman)](LICENSE)
[![ci](https://github.com/FNNDSC/pman/actions/workflows/ci.yml/badge.svg)](https://github.com/FNNDSC/pman/actions/workflows/ci.yml)

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

### Using Podman

_pman_ must be able to schedule containers via Podman by communicating to the Podman socket.

```shell
systemctl --user start podman.service
export DOCKER_HOST="$(podman info --format '{{ .Host.RemoteSocket.Path }}')"
```

### _pman_ On-the-Metal

```shell

```

## Configuration

_pman_ is configured by environment variables.
Refer to the source code in [pman/config.py](pman/config.py)
for exactly how it works.

### Configuration Overview

Before configuring pman for deployment, ask yourself two questions:

1. What `CONTAINER_ENV` am I using? (one of: Kubernetes, Docker Swarm, Docker Engine or Podman, Cromwell + SLURM)
2. How are data files shared across nodes in my compute cluster?

Storage in particular is tricky and there is no one-size-fits-all solution.
_pman_ and _pfcon_ are typically configured with an environment variable
[`STOREBASE`](#storebase). The historical context here is that the first
version of _pman_ was developed before Kubernetes was cool, so the best way
to share data files within a cluster was NFS. 

For multi-node clusters, the system administrator is expected to have an
existing solution for having a "shared volume" visible on the same path to
every node in the cluster (which is typically how NFS is used). The path on
each host to this share  should be provided as the value for `STOREBASE`.

For single-machine deployment using Podman or Docker Compose, the best solution
is to use a local volume, since the volume can be managed by the container engine
and is discoverable via the container engine's API. When `CONTAINER_ENV=docker`
(which is default since pman v4.1) and/or `STORAGE_TYPE=docker_host_volume`,
_pman_ will try to automatically discover what **existing** volume is the store base.

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

| Environment Variable | Description                                                             |
|----------------------|-------------------------------------------------------------------------|
| `SECRET_KEY`         | [Flask secret key][flask docs]                                          |
| `CONTAINER_ENV`      | one of: "swarm", "kubernetes", "cromwell", "docker"                     |
| `STORAGE_TYPE`       | one of: "host", "nfs", "docker_local_volume"                            |
| `STOREBASE`          | where job data is stored, [see below](#STOREBASE)                       |
| `VOLUME_NAME`        | name of local volume, valid when `STORAGE_TYPE=docker_local_volume`     |
| `PFCON_SELECTOR`     | label on the pfcon container (default: `org.chrisproject.role=pfcon`)   |
| `NFS_SERVER`         | NFS server address, required when `STORAGE_TYPE=nfs`                    |
| `JOB_LOGS_TAIL`      | (int) maximum size of job logs                                          |
| `REMOVE_JOBS`        | If set to "no" then pman will not delete jobs (debug)                   |

[flask docs]: https://flask.palletsprojects.com/en/2.1.x/config/#SECRET_KEY

### `STOREBASE`

- If `STORAGE_TYPE=host`, then `STOREBASE` represents the path on the
container host.
- If `STORAGE_TYPE=nfs`, then `STOREBASE` should be an exported NFS share
- If `STOREAGE_TYPE=docker_local_volume`,
  then _pman_ will try to figure it out for you

### `STOREAGE_TYPE=docker_local_volume`

For single-machine instances, use a Docker/Podman local volume as the "storeBase."
The volume should exist prior to the start of _pman_. It can be identified one of
two ways:

- Manually, by passing the volume name to the variable `VOLUME_NAME`
- Automatically: _pman_ inspects a container with the label `org.chrisproject.role=pfcon`
  and selects the mountpoint of the bind to `/var/local/storeBase`

### Kubernetes-Specific Options

Applicable when `CONTAINER_ENV=kubernetes`

| Environment Variable           | Description                                     |
|--------------------------------|-------------------------------------------------|
| `JOB_NAMESPACE`                | Kubernetes namespace for created jobs           |
| `SECURITYCONTEXT_RUN_AS_USER`  | Job container UID (NFS permissions workaround)  |
| `SECURITYCONTEXT_RUN_AS_GROUP` | Job container GID  (NFS permissions workaround) |

Currently, only HostPath and NFS volumes are supported.
_pfcon_ and _pman_ do not support (using nor creating) other kinds of PVCs.

### SLURM-Specific Options

Applicable when `CONTAINER_ENV=cromwell`

| Environment Variable | Description                                          |
|----------------------|------------------------------------------------------|
| `CROMWELL_URL`       | Cromwell URL                                         |
| `TIMELIMIT_MINUTES`  | SLURM job time limit                                 |

For how it works, see https://github.com/FNNDSC/pman/wiki/Cromwell

## TODO

- [ ] Dev environment and testing for Kubernetes and SLURM.
