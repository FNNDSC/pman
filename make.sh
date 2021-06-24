#!/bin/bash
#
# NAME
#
#   make.sh
#
# SYNPOSIS
#
#   make.sh                     [-h] [-i] [-s] [-U]     \
#                               [-O <swarm|kubernetes>] \
#                               [-S <storeBase>]        \
#                               [local|fnndsc[:dev]]
#
# DESC
#
#   'make.sh' sets up a pman development instance running either on Swarm or Kubernetes.
#   It can also optionally create a pattern of directories and symbolic links that
#   reflect the declarative environment on the orchestrator's service configuration file.
#
# TYPICAL CASES:
#
#   Run full pman instantiation on Swarm:
#
#       unmake.sh ; sudo rm -fr CHRIS_REMOTE_FS; rm -fr CHRIS_REMOTE_FS; make.sh
#
#   Skip the intro:
#
#       unmake.sh ; sudo rm -fr CHRIS_REMOTE_FS; rm -fr CHRIS_REMOTE_FS; make.sh -s
#
#
#   Run full pman instantiation on Kubernetes:
#
#       unmake.sh -O kubernetes; sudo rm -fr CHRIS_REMOTE_FS; rm -fr CHRIS_REMOTE_FS; make.sh -O kubernetes
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
#   -S <storeBase>
#
#       Explicitly set the STOREBASE dir to <storeBase>. This is the remote ChRIS
#       filesystem where plugins get their input data and create their output data.
#
#   -i
#
#       Optional do not automatically attach interactive terminal to pman container.
#
#   -U
#
#       Optional skip the UNIT tests.
#
#   -s
#
#       Optional skip intro steps. This skips the check on latest versions
#       of containers and the interval version number printing. Makes for
#       slightly faster startup.
#
#   [local|fnndsc[:dev]] (optional, default = 'fnndsc')
#
#       If specified, denotes the container "family" to use.
#
#       If a colon suffix exists, then this is interpreted to further
#       specify the TAG, i.e :dev in the example above.
#
#       The 'fnndsc' family are the containers as hosted on docker hub.
#       Using 'fnndsc' will always attempt to pull the latest container first.
#
#       The 'local' family are containers that are assumed built on the local
#       machine and assumed to exist. The 'local' containers are used when
#       'pman' service is being locally developed/debugged.
#
#

source ./decorate.sh
source ./cparse.sh

declare -i STEP=0
ORCHESTRATOR=swarm
HERE=$(pwd)

print_usage () {
    echo "Usage: ./make.sh [-h] [-i] [-s] [-U] [-S <storeBase>] [-O <swarm|kubernetes>] [local|fnndsc[:dev]]"
    exit 1
}

while getopts ":hsiUO:S:" opt; do
    case $opt in
        h) print_usage
           ;;
        s) b_skipIntro=1
          ;;
        i) b_norestartinteractive_pman_dev=1
          ;;
        U) b_skipUnitTests=1
          ;;
        O) ORCHESTRATOR=$OPTARG
           if ! [[ "$ORCHESTRATOR" =~ ^(swarm|kubernetes)$ ]]; then
              echo "Invalid value for option -- O"
              print_usage
           fi
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

if (( $# == 1 )) ; then
    REPO=$1
    export PMANREPO=$(echo $REPO | awk -F \: '{print $1}')
    export TAG=$(echo $REPO | awk -F \: '{print $2}')
    if (( ${#TAG} )) ; then
        TAG=":$TAG"
    fi
else
  export PMANREPO=fnndsc
  export TAG=
fi

declare -a A_CONTAINER=(
    "fnndsc/pman:dev^PMANREPO"
    "fnndsc/pl-simplefsapp"
)

title -d 1 "Setting global exports..."
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
    echo -e "ORCHESTRATOR=$ORCHESTRATOR"                 | ./boxes.sh
    echo -e "exporting STOREBASE=$STOREBASE "            | ./boxes.sh
    export STOREBASE=$STOREBASE
    export SOURCEDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
    echo -e "exporting SOURCEDIR=$SOURCEDIR "                           | ./boxes.sh
windowBottom

if (( ! b_skipIntro )) ; then
    title -d 1 "Pulling non-'local/' core containers where needed..."
    for CORE in ${A_CONTAINER[@]} ; do
        cparse $CORE " " "REPO" "CONTAINER" "MMN" "ENV"
        if [[ $REPO != "local" ]] ; then
            echo ""                                                 | ./boxes.sh
            CMD="docker pull ${REPO}/$CONTAINER"
            printf "${LightCyan}%-40s${Green}%40s${Yellow}\n"       \
                        "docker pull" "${REPO}/$CONTAINER"          | ./boxes.sh
            windowBottom
            sleep 1
            echo $CMD | sh                                          | ./boxes.sh -c
        fi
    done
    windowBottom
fi

title -d 1 "Changing permissions to 755 on" "$HERE"
    cd $HERE
    echo "chmod -R 755 $HERE"                                      | ./boxes.sh
    chmod -R 755 $HERE
windowBottom

title -d 1 "Checking that STOREBASE directory" "$STOREBASE is empty..."
    chmod -R 777 $STOREBASE
    b_FSOK=1
    type -all tree >/dev/null 2>/dev/null
    if (( ! $? )) ; then
        tree $STOREBASE                                                    | ./boxes.sh
        report=$(tree $STOREBASE | tail -n 1)
        if [[ "$report" != "0 directories, 0 files" ]] ; then
            b_FSOK=0
        fi
    else
        report=$(find $STOREBASE 2>/dev/null)
        lines=$(echo "$report" | wc -l)
        if (( lines != 1 )) ; then
            b_FSOK=0
        fi
        echo "lines is $lines"
    fi
    if (( ! b_FSOK )) ; then
        printf "The STOREBASE directory $STOREBASE must be empty!\n"    | ./boxes.sh ${Red}
        printf "Please manually clean it and re-run.\n"      | ./boxes.sh ${Yellow}
        printf "\nThis script will now exit with code '1'.\n\n"                     | ./boxes.sh ${Yellow}
        exit 1
    fi
    printf "${LightCyan}%40s${LightGreen}%40s\n"                    \
                "Tree state" "[ OK ]"                               | ./boxes.sh
windowBottom

title -d 1 "Starting pman containerized dev environment on $ORCHESTRATOR"
    if [[ $ORCHESTRATOR == swarm ]]; then
        echo "docker stack deploy -c swarm/docker-compose_dev.yml pman_dev_stack" | ./boxes.sh ${LightCyan}
        docker stack deploy -c swarm/docker-compose_dev.yml pman_dev_stack
    elif [[ $ORCHESTRATOR == kubernetes ]]; then
        echo "envsubst < kubernetes/pman_dev.yaml | kubectl apply -f -"           | ./boxes.sh ${LightCyan}
        envsubst < kubernetes/pman_dev.yaml | kubectl apply -f -
    fi
windowBottom

title -d 1 "Waiting until pman container is running on $ORCHESTRATOR"
    echo "This might take a few minutes... please be patient."      | ./boxes.sh ${Yellow}
    for i in {1..30}; do
        sleep 5
        if [[ $ORCHESTRATOR == swarm ]]; then
            pman_dev=$(docker ps -f label=org.chrisproject.role=pman -q | head -n 1)
        elif [[ $ORCHESTRATOR == kubernetes ]]; then
            pman_dev=$(kubectl get pods --selector="app=pman,env=development" --field-selector=status.phase=Running --output=jsonpath='{.items[*].metadata.name}')
        fi
        if [ -n "$pman_dev" ]; then
          echo "Success: pman container is up"           | ./boxes.sh ${Green}
          break
        fi
    done
    if [ -z "$pman_dev" ]; then
        echo "Error: couldn't start pman container"      | ./boxes.sh ${Red}
        exit 1
    fi
windowBottom

if (( ! b_skipUnitTests )) ; then
    title -d 1 "Running pman tests..."
    sleep 5
    if [[ $ORCHESTRATOR == swarm ]]; then
        docker exec $pman_dev nosetests --exe tests
    elif [[ $ORCHESTRATOR == kubernetes ]]; then
        kubectl exec $pman_dev -- nosetests --exe tests
    fi
    status=$?
    title -d 1 "pman test results"
    if (( $status == 0 )) ; then
        printf "%40s${LightGreen}%40s${NC}\n"                       \
            "pman tests" "[ success ]"                         | ./boxes.sh
    else
        printf "%40s${Red}%40s${NC}\n"                              \
            "pman tests" "[ failure ]"                         | ./boxes.sh
    fi
    windowBottom
fi

if (( !  b_norestartinteractive_pman_dev )) ; then
    title -d 1 "Attaching interactive terminal (ctrl-c to detach)"
    if [[ $ORCHESTRATOR == swarm ]]; then
        docker logs $pman_dev
        docker attach --detach-keys ctrl-c $pman_dev
    elif [[ $ORCHESTRATOR == kubernetes ]]; then
        kubectl logs $pman_dev
        kubectl attach $pman_dev -i -t
    fi
fi
