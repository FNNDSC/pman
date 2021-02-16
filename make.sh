#!/bin/bash
#
# NAME
#
#   make.sh
#
# SYNPOSIS
#
#   make.sh                     [-r <service>]                  \
#                               [-a <swarm-advertise-adr>]      \
#                               [-p] [-i] [-s]                  \
#                               [-S <storeBaseOverride>]        \
#                               [local|fnndsc[:dev]]
#
# DESC
#
#   'make.sh' sets up a pman development instance using docker-compose.
#   It can also optionally create a pattern of directories and symbolic links
#   that reflect the declarative environment of the docker-compose contents.
#
# TYPICAL CASES:
#
#   Run full pfcom instantiation:
#
#       unmake.sh ; sudo rm -fr FS; rm -fr FS; make.sh
#
#   Skip the intro:
#
#       unmake.sh ; sudo rm -fr FS; rm -fr FS; make.sh -s
#
# ARGS
#
#
#   -r <service>
#
#       Restart <service> in interactive mode. This is mainly for debugging
#       and is typically used to restart the 'pman' service.
#
#   -S <storeBaseOverride>
#
#       Explicitly set the STOREBASE dir to <storeBaseOverride>. This is useful
#       mostly in non-Linux hosts (like macOS) where there might be a mismatch
#       between the actual STOREBASE path and the text of the path shared between
#       the macOS host and the docker VM.
#
#   -a <swarm-advertise-adr>
#
#       If specified, pass <swarm-advertise-adr> to swarm init.
#
#   -i
#
#       Optional do not restart final pman in interactive mode.
#
#   -s
#
#       Optional skip intro steps. This skips the check on latest versions
#       of containers and the interval version number printing. Makes for
#       slightly faster startup.
#
#   -p
#
#       Optional pause after instantiating system to allow user to stop
#       and restart services in interactive mode. User stops and restarts
#       services explicitly with
#
#               docker stop <ID> && docker rm -vf <ID> && *make* -r <service>
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
declare -i b_restart=0
JOB=""
HERE=$(pwd)
echo "Starting script in dir $HERE"

CREPO=fnndsc
TAG=

if [[ -f .env ]] ; then
    source .env
fi

while getopts "r:psiUa:S:" opt; do
    case $opt in
        r) b_restart=1
           JOB=$OPTARG                          ;;
        p) b_pause=1                            ;;
        s) b_skipIntro=1                        ;;
        i) b_norestartinteractive_chris_dev=1   ;;
        a) b_swarmAdvertiseAdr=1
            SWARMADVERTISEADDR=$OPTARG          ;;
        U) b_skipUnitTests=1                    ;;
        S) b_storeBaseOverride=1
           STOREBASE=$OPTARG                    ;;
    esac
done

shift $(($OPTIND - 1))
if (( $# == 1 )) ; then
    REPO=$1
    export CREPO=$(echo $REPO | awk -F \: '{print $1}')
    export TAG=$(echo $REPO | awk -F \: '{print $2}')
    if (( ${#TAG} )) ; then
        TAG=":$TAG"
    fi
fi

declare -a A_CONTAINER=(
    "fnndsc/pman:dev^PMANREPO"
    "fnndsc/pl-simplefsapp"
)

title -d 1 "Setting global exports..."
    if (( ! b_storeBaseOverride )) ; then
        if [[ ! -d FS/remote ]] ; then
            mkdir -p FS/remote
        fi
        cd FS/remote
        STOREBASE=$(pwd)
        cd $HERE
    fi
    echo -e "${STEP}.1 For pman override to swarm containers,"          | ./boxes.sh
    echo -e "exporting STOREBASE=$STOREBASE "                           | ./boxes.sh
    export STOREBASE=$STOREBASE
windowBottom

if (( b_restart )) ; then
    title -d 1 "Restarting ${JOB} service"                              \
                    "in interactive mode..."
    printf "${LightCyan}%40s${LightGreen}%40s\n"                        \
                "Stopping" "${JOB}_service"                             | ./boxes.sh
    windowBottom

    docker-compose -f docker-compose_dev.yml --no-ansi                  \
        stop ${JOB}_service >& dc.out > /dev/null
    echo -en "\033[2A\033[2K"
    cat dc.out | ./boxes.sh

    printf "${LightCyan}%40s${LightGreen}%40s\n"                        \
                "rm -f" "${JOB}_service"                                | ./boxes.sh
    windowBottom

    docker-compose -f docker-compose_dev.yml --no-ansi                  \
        rm -f ${JOB}_service >& dc.out > /dev/null
    echo -en "\033[2A\033[2K"
    cat dc.out | ./boxes.sh
    windowBottom

    docker-compose -f docker-compose_dev.yml --no-ansi                  \
        run --service-ports ${JOB}_service
else
    title -d 1 "Pulling non-'local/' core containers where needed..."   \
                "and creating appropriate .env for docker-compose_dev.yml"
    if (( ! b_skipIntro )) ; then
        echo "# Variables declared here are available to"               > .env
        echo "# docker-compose -f docker-compose_dev.yml on execution"                            >>.env
        for CORE in ${A_CONTAINER[@]} ; do
            cparse $CORE " " "REPO" "CONTAINER" "MMN" "ENV"
            echo "${ENV}=${REPO}"                                       >>.env
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
        echo "TAG="                                                     >>.env
    fi
    windowBottom

    if (( ! b_skipIntro )) ; then
        title -d 1 "Will use containers with following version info:"
        for CORE in ${A_CONTAINER[@]} ; do
            cparse $CORE " " "REPO" "CONTAINER" "MMN" "ENV"
            if [[   $CONTAINER != "pl-simplefsapp"  ]] ; then
                windowBottom
                CMD="docker run ${REPO}/$CONTAINER --version"
                Ver=$(echo $CMD | sh | grep Version)
                echo -en "\033[2A\033[2K"
                printf "${White}%40s${Green}%40s${Yellow}\n"            \
                        "${REPO}/$CONTAINER" "$Ver"                     | ./boxes.sh
            fi
        done
    fi

    title -d 1 "Stopping and restarting the docker swarm... "
        docker swarm leave --force >dc.out 2>dc.out
        cat dc.out | ./boxes.sh
        if (( b_swarmAdvertiseAdr )) ; then
            docker swarm init --advertise-addr=$SWARMADVERTISEADDR      |\
                sed 's/[[:alnum:]]+:/\n&/g' | sed -E 's/(.{80})/\1\n/g' | ./boxes.sh
        else
            docker swarm init --advertise-addr 127.0.0.1                |\
                sed 's/[[:alnum:]]+:/\n&/g' | sed -E 's/(.{80})/\1\n/g' | ./boxes.sh
        fi
        echo "Swarm started"                                            | ./boxes.sh
    windowBottom

    title -d 1 "Shutting down any running pman and related containers... "
        echo "This might take a few minutes... please be patient."              | ./boxes.sh ${Yellow}
        windowBottom
        docker-compose -f docker-compose_dev.yml --no-ansi                      \
            stop >& dc.out > /dev/null
        echo -en "\033[2A\033[2K"
        cat dc.out | sed -E 's/(.{80})/\1\n/g'                                  | ./boxes.sh ${LightBlue}
        docker-compose -f docker-compose_dev.yml --no-ansi                      \
            rm -vf >& dc.out > /dev/null
        cat dc.out | sed -E 's/(.{80})/\1\n/g'                                  | ./boxes.sh ${LightCyan}
        for CORE in ${A_CONTAINER[@]} ; do
            cparse $CORE " " "REPO" "CONTAINER" "MMN" "ENV"
            docker ps -a                                                        |\
                grep $CONTAINER                                                 |\
                awk '{printf("docker stop %s && docker rm -vf %s\n", $1, $1);}' |\
                sh >/dev/null                                                   | ./boxes.sh
            printf "${White}%40s${Green}%40s${NC}\n"                            \
                        "$CONTAINER" "stopped"                                  | ./boxes.sh
        done
    windowBottom

    title -d 1 "Changing permissions to 755 on" "$(pwd)"
        cd $HERE
        echo "chmod -R 755 $(pwd)"                                      | ./boxes.sh
        chmod -R 755 $(pwd)
    windowBottom

    title -d 1 "Checking that FS directory tree is empty..."
        mkdir -p FS/remote
        chmod -R 777 FS
        b_FSOK=1
        type -all tree >/dev/null 2>/dev/null
        if (( ! $? )) ; then
            tree FS                                                     | ./boxes.sh
            report=$(tree FS | tail -n 1)
            if [[ "$report" != "1 directory, 0 files" ]] ; then
                b_FSOK=0
            fi
        else
            report=$(find FS 2>/dev/null)
            lines=$(echo "$report" | wc -l)
            if (( lines != 2 )) ; then
                b_FSOK=0
            fi
            echo "lines is $lines"
        fi
        if (( ! b_FSOK )) ; then
            printf "There should only be 1 directory and no files in the FS tree!\n"    | ./boxes.sh ${Red}
            printf "Please manually clean/delete the entire FS tree and re-run.\n"      | ./boxes.sh ${Yellow}
            printf "\nThis script will now exit with code '1'.\n\n"                     | ./boxes.sh ${Yellow}
            exit 1
        fi
        printf "${LightCyan}%40s${LightGreen}%40s\n"                    \
                    "Tree state" "[ OK ]"                               | ./boxes.sh
    windowBottom

    title -d 1 "Starting pman containerized development environment "
        echo "This might take a few minutes... please be patient."      | ./boxes.sh ${Yellow}
        echo "docker-compose -f docker-compose_dev.yml  up -d"          | ./boxes.sh ${LightCyan}
        windowBottom
        docker-compose -f docker-compose_dev.yml --no-ansi              \
            up -d >& dc.out > /dev/null
        echo -en "\033[2A\033[2K"
        cat dc.out | sed -E 's/(.{80})/\1\n/g'                          | ./boxes.sh ${LightGreen}
    windowBottom

    if (( ! b_skipUnitTests )) ; then
        title -d 1 "Running pman tests..."
        echo "This might take a few minutes... please be patient."      | ./boxes.sh ${Yellow}
        windowBottom
        docker-compose -f docker-compose_dev.yml exec pman_service nosetests --exe tests
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

    title -d 1 "Pause for manual restart of services?"
    if (( b_pause )) ; then
        echo "Pausing... hit *ANY* key to continue"                     | ./boxes.sh
        windowBottom
        old_stty_cfg=$(stty -g)
        stty raw -echo ; REPLY=$(head -c 1) ; stty $old_stty_cfg
        echo -en "\033[2A\033[2K"
        echo "Resuming..."                                              | ./boxes.sh
    fi
    windowBottom


    if (( !  b_norestartinteractive_chris_dev )) ; then
        title -d 1 "Restarting pman development server"                \
                            "in interactive mode..."
            printf "${LightCyan}%40s${LightGreen}%40s\n"                \
                        "Stopping" "pman_service"                      | ./boxes.sh
            windowBottom
            docker-compose -f docker-compose_dev.yml --no-ansi          \
                stop pman_service >& dc.out > /dev/null
            echo -en "\033[2A\033[2K"
            cat dc.out | ./boxes.sh

            printf "${LightCyan}%40s${LightGreen}%40s\n"                \
                        "rm -f" "pman_service"                         | ./boxes.sh
            windowBottom
            docker-compose -f docker-compose_dev.yml --no-ansi          \
                rm -f pman_service >& dc.out > /dev/null
            echo -en "\033[2A\033[2K"
            cat dc.out | ./boxes.sh


            printf "${LightCyan}%40s${LightGreen}%40s\n"                \
                        "Starting in interactive mode" "pman"          |./boxes.sh
            windowBottom
            docker-compose -f docker-compose_dev.yml                    \
                run --service-ports pman_service
    fi

fi
