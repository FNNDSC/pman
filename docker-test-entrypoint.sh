#!/bin/bash -e
# Helper script for testing pman on single-machine docker swarm with docker-compose.

py="
import os
import sys
import docker

d = docker.from_env()

def by_label(label):
    return d.containers.list(filters={'label': f'org.chrisproject.role={label}'})[0]

pman = by_label('pman-testing')
storebase = [v['Source'] for v in pman.attrs['Mounts'] if v['Destination'] == '/var/local/storeBase'][0]
print(storebase)
"

export STOREBASE="$(python -c "$py")"
>&2 echo "Detected host path of STOREBASE=$STOREBASE"

export STORAGE_TYPE=host APPLICATION_MODE=development CONTAINER_ENV=swarm PYTHONDONTWRITEBYTECODE=1

if [ "$#" -eq 0 ]; then
  set -x
  exec python -m pman
fi

exec "$@"
