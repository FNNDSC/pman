#!/bin/bash
#
# NAME
#
#   deploy.sh
#
# SYNPOSIS
#
#   deploy.sh                   [-h]
#                               [-O <swarm|kubernetes>] \
#                               [-N <namespace>]        \
#                               [-T <host|nfs>]      \
#                               [-P <nfsServerIp>]      \
#                               [-S <storeBase>]        \
#                               [up|down]
#
# DESC
#
#   'deploy.sh' script will depending on the argument deploy pman services in production 
#   or tear down the system.
#
# TYPICAL CASES:
#
#   Deploy pman service into a Swarm cluster:
#
#       deploy.sh up
#
#
#   Deploy pman service into a Kubernetes cluster:
#
#       deploy.sh -O kubernetes up
#
# ARGS
#
#
#   -h
#
#       Optional print usage help.
#
#   -O <swarm|kubernetes>
#
#       Explicitly set the orchestrator. Default is swarm.
#
#   -N <namespace>
#
#       Explicitly set the kubernetes namespace to <namespace>. Default is chris.
#       Not used for swarm.
#
#   -T <host|nfs>
#
#       Explicitly set the storage type for the STOREBASE dir. Default is host.
#       Note: The nfs storage type is not implemented for swarm orchestrator yet.
#
#   -P <nfsServerIp>
#
#       Set the IP address of the NFS server. Required when storage type is set to 'nfs'.
#       Not used for 'host' storage type.
#
#   -S <storeBase>
#
#       Explicitly set the STOREBASE dir to <storeBase>. This is the remote ChRIS
#       filesystem where pfcon and plugins share data (usually externally mounted NFS).
#
#   [up|down] (optional, default = 'up')
#
#       Denotes whether to fire up or tear down the production service.
#
#


source ./decorate.sh
source ./cparse.sh

declare -i STEP=0
ORCHESTRATOR=swarm
NAMESPACE=chris
STORAGE_TYPE=host
HERE=$(pwd)

print_usage () {
    echo "Usage: ./deploy.sh [-h] [-O <swarm|kubernetes>] [-N <namespace>] [-T <host|nfs>]
         [-P <nfsServerIp>] [-S <storeBase>] [up|down]"
    exit 1
}

while getopts ":hO:N:T:P:S:" opt; do
    case $opt in
        h) print_usage
           ;;
        O) ORCHESTRATOR=$OPTARG
           if ! [[ "$ORCHESTRATOR" =~ ^(swarm|kubernetes)$ ]]; then
              echo "Invalid value for option -- O"
              print_usage
           fi
           ;;
        N) NAMESPACE=$OPTARG
           ;;
        T) STORAGE_TYPE=$OPTARG
           if ! [[ "$STORAGE_TYPE" =~ ^(host|nfs)$ ]]; then
              echo "Invalid value for option -- T"
              print_usage
           fi
           ;;
        P) NFS_SERVER=$OPTARG
           ;;
        S) STOREBASE=$OPTARG
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

if [[ $STORAGE_TYPE == nfs ]]; then
    if [[ $ORCHESTRATOR == swarm ]]; then
        echo -e "Sorry, nfs storage type is not supported for swarm orchestrator yet"  | ./boxes.sh
        exit 1
    fi
    if [ -z ${NFS_SERVER+x} ]; then
        echo "-P <NFS_SERVER> (the NFS server ip address) must be specified or the shell
             environment variable NFS_SERVER must be set when using nfs storage type"
        print_usage
    fi
    if [ -z ${STOREBASE+x} ]; then
        echo "-S <storeBase> must be specified or the shell environment variable STOREBASE
             must be set when using nfs storage type"
        print_usage
    fi
fi

COMMAND=up
if (( $# == 1 )) ; then
    COMMAND=$1
    if ! [[ "$COMMAND" =~ ^(up|down)$ ]]; then
        echo "Invalid value $COMMAND"
        print_usage
    fi
fi

title -d 1 "Setting global exports..."
    if [[ $STORAGE_TYPE == host ]]; then
        if [ -z ${STOREBASE+x} ]; then
            if [[ ! -d CHRIS_REMOTE_FS ]] ; then
                mkdir CHRIS_REMOTE_FS
            fi
            STOREBASE=$HERE/CHRIS_REMOTE_FS
        else
            if [[ ! -d $STOREBASE ]] ; then
                mkdir -p $STOREBASE
            fi
        fi
    fi
    echo -e "ORCHESTRATOR=$ORCHESTRATOR"                          | ./boxes.sh
    echo -e "exporting STORAGE_TYPE=$STORAGE_TYPE"                | ./boxes.sh
    export STORAGE_TYPE=$STORAGE_TYPE
    if [[ $STORAGE_TYPE == nfs ]]; then
        echo -e "exporting NFS_SERVER=$NFS_SERVER"                | ./boxes.sh
        export NFS_SERVER=$NFS_SERVER
    fi
    echo -e "exporting STOREBASE=$STOREBASE"                      | ./boxes.sh
    export STOREBASE=$STOREBASE
    if [[ $ORCHESTRATOR == kubernetes ]]; then
        echo -e "exporting NAMESPACE=$NAMESPACE"                  | ./boxes.sh
        export NAMESPACE=$NAMESPACE
    fi
windowBottom

if [[ "$COMMAND" == 'up' ]]; then

    title -d 1 "Starting pman containerized prod environment on $ORCHESTRATOR"
    if [[ $ORCHESTRATOR == swarm ]]; then
        echo "docker stack deploy -c swarm/prod/docker-compose.yml pman_stack"   | ./boxes.sh ${LightCyan}
        docker stack deploy -c swarm/prod/docker-compose.yml pman_stack
    elif [[ $ORCHESTRATOR == kubernetes ]]; then
        echo "kubectl create namespace $NAMESPACE"   | ./boxes.sh ${LightCyan}
        namespace=$(kubectl get namespaces $NAMESPACE --no-headers -o custom-columns=:metadata.name 2> /dev/null)
        if [ -z "$namespace" ]; then
            kubectl create namespace $NAMESPACE
        else
            echo "$NAMESPACE namespace already exists, skipping creation"
        fi
        echo "kubectl kustomize kubernetes/prod | envsubst | kubectl apply -f -"  | ./boxes.sh ${LightCyan}
        kubectl kustomize kubernetes/prod | envsubst | kubectl apply -f -
    fi
    windowBottom
fi

if [[ "$COMMAND" == 'down' ]]; then

    title -d 1 "Destroying pman containerized prod environment on $ORCHESTRATOR"
    if [[ $ORCHESTRATOR == swarm ]]; then
        echo "docker stack rm pman_stack"                               | ./boxes.sh ${LightCyan}
        docker stack rm pman_stack
    elif [[ $ORCHESTRATOR == kubernetes ]]; then
        echo "kubectl kustomize kubernetes/prod | envsubst | kubectl delete -f -"  | ./boxes.sh ${LightCyan}
        kubectl kustomize kubernetes/prod | envsubst | kubectl delete -f -
    fi
    windowBottom
fi
