#!/bin/bash
# sets STOREBASE based on a docker named volume,
# specified by PMAN_DOCKER_VOLUME.
#
# Typically, PMAN_DOCKER_VOLUME would be mounted by
# pfioh to be used as "--storeBase"
# for single-machine docker-compose managed setups.
# tip: the volume does not need to be mounted inside pman

get_volume_mountpoint_py="
import docker
d = docker.from_env()
v = d.volumes.get('$PMAN_DOCKER_VOLUME')
print(v.attrs['Mountpoint'])
"

if [ ! -v STOREBASE ] && [ -n "$PMAN_DOCKER_VOLUME" ]; then
  if mountpoint=$(python -c "$get_volume_mountpoint_py"); then
    export STOREBASE=$mountpoint
  fi
fi

exec pman $@
