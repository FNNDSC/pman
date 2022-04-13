#!/bin/bash -ex
# test pman on single-machine docker swarm

docker swarm init --advertise-addr 127.0.0.1

docker-compose build

docker stack deploy -c docker-compose.yml pman_dev

for i in {0..4}; do
  sleep 1
  container_id=$(docker ps -f label=org.chrisproject.role=pman-testing -q | head -n 1)
  if [ -n "$container_id" ]; then
    break
  fi
done
if [ -z "$container_id" ]; then
  echo "pman failed to start."
fi

docker exec -it $container_id ./docker-test-entrypoint.sh pytest

docker stack rm pman_dev
docker swarm leave --force

# on Docker version 20.10.3, build 48d30b5, I have a bug where I need to restart dockerd to
# remove the dangling network created by docker swarm.
#
#     systemctl restart docker
