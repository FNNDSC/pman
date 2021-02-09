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
    export STOREBASE="$mountpoint"
  fi
fi

# While STOREBASE is a workaround for working with the swarm scheduler,
# we can borrow some advice from OpenShift.
#
# The user of a container is always a member of the group with GID=0
#
# By granting the root (GID=0) group rw (read-write) permission to STOREBASE,
# we can run ChRIS plugin containers as underprivileged users with arbitrary UID
# and still allow them to write to the shared directories (volume mounts).
#
# https://www.openshift.com/blog/a-guide-to-openshift-and-uids
# https://docs.openshift.com/container-platform/3.3/creating_images/guidelines.html#openshift-container-platform-specific-guidelines

if [ -d "$STOREBASE" ]; then
  chgrp -R 0 "$STOREBASE"
  chmod -R g+rw "$STOREBASE"
fi

exec pman $@
