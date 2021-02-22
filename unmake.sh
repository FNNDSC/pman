#!/bin/bash

source ./decorate.sh

declare -i STEP=0

export STOREBASE=${STOREBASE}

title -d 1 "Destroying pman containerized development environment" \
                    "from ./docker-compose_dev.yml..."
    docker-compose -f docker-compose_dev.yml --no-ansi down >& dc.out >/dev/null
    cat dc.out                                                              | ./boxes.sh
    echo "Removing ./FS tree"                                               | ./boxes.sh
    rm -fr ./FS
windowBottom

title -d 1 "Stopping swarm cluster..."
    docker swarm leave --force >dc.out 2>dc.out
    cat dc.out                                                              | ./boxes.sh
windowBottom
