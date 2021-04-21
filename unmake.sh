#!/bin/bash
#
# NAME
#
#   unmake.sh
#
# SYNPOSIS
#
#   make.sh                     [-O <swarm|kubernetes>]
#
#
# DESC
#
#   'unmake.sh' destroys a pman development instance running on Swarm or Kubernetes.
#
# TYPICAL CASES:
#
#   Destroy pman dev instance on Swarm:
#
#       unmake.sh
#
#   Destroy pman dev instance on Kubernetes:
#
#       unmake.sh -O kubernetes
#
# ARGS
#
#
#   -O <swarm|kubernetes>
#
#       Explicitly set the orchestrator. Default is swarm.
#
#

source ./decorate.sh

declare -i STEP=0
ORCHESTRATOR=swarm

print_usage () {
    echo "Usage: ./unmake.sh [-O <swarm|kubernetes>]"
    exit 1
}

while getopts ":O:" opt; do
    case $opt in
        O) ORCHESTRATOR=$OPTARG
           if ! [[ "$ORCHESTRATOR" =~ ^(swarm|kubernetes)$ ]]; then
              echo "Invalid value for option -- O"
              print_usage
           fi
           ;;
        \?) echo "Invalid option -- $OPTARG"
            print_usage
            ;;
        :) echo "Option requires an argument -- $OPTARG"
           print_usage
           ;;
    esac
done
shift $(($OPTIND - 1))

title -d 1 "Destroying pman containerized dev environment on $ORCHESTRATOR"
    if [[ $ORCHESTRATOR == swarm ]]; then
        echo "docker stack rm pman_dev_stack"                               | ./boxes.sh ${LightCyan}
        windowBottom
        docker stack rm pman_dev_stack >& dc.out >/dev/null
    elif [[ $ORCHESTRATOR == kubernetes ]]; then
        echo "kubectl delete -f kubernetes/pman_dev.yaml"                   | ./boxes.sh ${LightCyan}
        windowBottom
        kubectl delete -f kubernetes/pman_dev.yaml >& dc.out >/dev/null
    fi
    echo -en "\033[2A\033[2K"
    cat dc.out | sed -E 's/(.{80})/\1\n/g'                          | ./boxes.sh ${LightGreen}
    echo "Removing ./FS tree"                                       | ./boxes.sh
    rm -fr ./FS
windowBottom
