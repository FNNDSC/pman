#!/bin/bash

source ./decorate.sh

declare -i STEP=0

export STOREBASE=${STOREBASE}

title -d 1 "Destroying pman_dev_stack containerized dev environment on Swarm"
    echo "This might take a few minutes... please be patient."      | ./boxes.sh ${Yellow}
    echo "docker stack rm pman_dev_stack"                               | ./boxes.sh ${LightCyan}
    windowBottom
    docker stack rm pman_dev_stack >& dc.out >/dev/null
    echo -en "\033[2A\033[2K"
    cat dc.out | sed -E 's/(.{80})/\1\n/g'                          | ./boxes.sh ${LightGreen}
    echo "Removing ./FS tree"                                       | ./boxes.sh
    rm -fr ./FS
windowBottom
