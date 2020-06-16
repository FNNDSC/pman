#!/bin/bash
#
# NAME
#
#   make.sh
#
# SYNPOSIS
#
#   make.sh                     [-k|-r <service>]               \
#                               [-a <swarm-advertise-adr>]      \
#                               [-p] [-s] [-i] [-d]             \
#                               [-U] [-I]                       \
#                               [-S <storeBaseOverride>]        \
#                               [-e <computeEnv>]               \
#                               [local|fnndsc[:dev]]
#
# DESC
#
#   'make.sh' is the main entry point for instantiating a
#   stand-alone `pman` environment.
#
# TYPICAL CASES:
#
#   Run the `pman` instantiation with tests:
#
#       unmake.sh ; sudo rm -fr FS; rm -fr FS; make.sh
#
#
# ARGS
#
#   -U
#
#       Skip the UNIT tests.
#
#   -I
#
#       Skip the INTEGRATION tests.
#
#   -S <storeBaseOverride>
#
#       Explicitly set the STOREBASE dir to <storeBaseOverride>. This is useful
#       mostly in non-Linux hosts (like macOS) where there might be a mismatch
#       between the actual STOREBASE path and the text of the path shared between
#       the macOS host and the docker VM.
#
#   -r <service>
#
#       Restart <service> in interactive mode. This is mainly for debugging
#       and is typically used to restart the 'pfcon', 'pfioh', and 'pman'
#       services.
#
#   -e <computeEnv>
#
#       Register all plugins to the passed <computeEnv>. Note, this is simply
#       an index string that is actually defined in `pfcon`. In other words,
#       the <computeEnv> here is just a label, and the actual env is fully
#       specified by `pfcon`.
#
#   -a <swarm-advertise-adr>
#
#       If specified, pass <swarm-advertise-adr> to swarm init.
#
#   -i
#
#       Optional do not restart final chris_dev in interactive mode. If any
#       sub services have been restarted in interactive mode then this will
#       break the final restart of the chris_dev container. Thus, if any
#       services have been restarted with '-r <service>' it is recommended
#       to also use this flag to avoid the chris_dev restart.
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
#   -d
#
#       Optional debug ON. If specified, trigger verbose output during
#       run, especially during testing. Useful for debugging.
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
#       the 'pfcon/pman/pfioh/pfurl' services are being locally
#       developed/debugged.
#
#

source ./decorate.sh
source ./cparse.sh

declare -i STEP=0
declare -i b_restart=0
declare -i b_kill=0

# declare -i b_pause=0
# declare -i b_skipIntro=0
# declare -i b_norestartinteractive_chris_dev=0
# declare -i b_debug=0
# declare -i b_swarmAdvertiseAdr=0
# declare -i b_storeBaseOverride=0
# COMPUTEENV="host"
# SWARMADVERTISEADDR=""
# RESTART=""
HERE=$(pwd)
# LINE="------------------------------------------------"
# echo ""
# echo "Starting script in dir $HERE"

CREPO=fnndsc
TAG=

if [[ -f .env ]] ; then
    source .env
fi

while getopts "k:r:psidUIa:S:" opt; do
    case $opt in
        r) b_restart=1
           RESTART=$OPTARG                      ;;
        k) b_kill=1
           RESTART=$OPTARG                      ;;
        p) b_pause=1                            ;;
        s) b_skipIntro=1                        ;;
        i) b_norestartinteractive_chris_dev=1   ;;
        a) b_swarmAdvertiseAdr=1
            SWARMADVERTISEADDR=$OPTARG          ;;
        d) b_debug=1                            ;;
        U) b_skipUnitTests=1                    ;;
        I) b_skipIntegrationTests=1             ;;
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
    "${CREPO}/pman${TAG}^PMANREPO"
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
    echo -e "${STEP}.1 For pman override to swarm containers, exporting\nSTOREBASE=$STOREBASE " | ./boxes.sh
    export STOREBASE=$STOREBASE
    if (( b_debug )) ; then
        echo -e "${STEP}.2 Setting debug quiet to OFF. Note this is noisy!" | ./boxes.sh
        export CHRIS_DEBUG_QUIET=0
    fi
windowBottom

if (( b_restart || b_kill )) ; then
    printf "${Red}Stopping $JOB...${NC}\n"
    docker-compose -f docker-compose.yml stop                           \
        ${RESTART}_service && docker-compose -f docker-compose.yml      \
        rm -f ${RESTART}_service                                        > dc.out
        cat dc.out | ./boxes.sh

    docker-compose -f docker-compose.yml run --service-ports            \
        ${RESTART}_service                                              > dc.out
        cat dc.out | ./boxes.sh
else
    title -d 1 "Pulling non-'local/' core containers where needed..."   \
                "and creating appropriate .env for docker-compose"
    if (( ! b_skipIntro )) ; then
        echo "# Variables declared here are available to"               > .env
        echo "# docker-compose on execution"                            >>.env
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
            windowBottom
            CMD="docker run --rm ${REPO}/$CONTAINER --version"
            Ver=$(echo $CMD | sh | grep Version)
            echo -en "\033[2A\033[2K"
            printf "${White}%40s${Green}%40s${Yellow}\n"            \
                    "${REPO}/$CONTAINER" "$Ver"                     | ./boxes.sh
        done
        windowBottom
    fi

    title -d 1 "Shutting down any running pman and pman related containers... "
        echo "This might take a few minutes... please be patient."              | ./boxes.sh ${Yellow}
        windowBottom
        docker-compose --no-ansi -f docker-compose.yml stop >& dc.out > /dev/null
        echo -en "\033[2A\033[2K"
        cat dc.out | sed -E 's/(.{80})/\1\n/g'                                  | ./boxes.sh ${LightBlue}
        docker-compose --no-ansi -f docker-compose.yml rm -vf >& dc.out > /dev/null
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
        mkdir -p FS/local
        mkdir -p FS/remote
        mkdir -p FS/data
        chmod -R 777 FS
        b_FSOK=1
        type -all tree >/dev/null 2>/dev/null
        if (( ! $? )) ; then
            tree FS                                                     | ./boxes.sh
            report=$(tree FS | tail -n 1)
            if [[ "$report" != "3 directories, 0 files" ]] ; then
                b_FSOK=0
            fi
        else
            report=$(find FS 2>/dev/null)
            lines=$(echo "$report" | wc -l)
            if (( lines != 4 )) ; then
                b_FSOK=0
            fi
        fi
        if (( ! b_FSOK )) ; then
            printf "There should only be 3 directories and no files in the FS tree!\n"  | ./boxes.sh ${Red}
            printf "Please manually clean/delete the entire FS tree and re-run.\n"      | ./boxes.sh ${Yellow}
            printf "\nThis script will now exit with code '1'.\n\n"                     | ./boxes.sh ${Yellow}
            exit 1
        fi
        printf "${LightCyan}%40s${LightGreen}%40s\n"                    \
                    "Tree state" "[ OK ]"                               | ./boxes.sh
    windowBottom

    title -d 1 "Starting pman containerized development environment using "\
                        "./docker-compose.yml"
        echo "This might take a few minutes... please be patient."      | ./boxes.sh ${Yellow}
        echo "docker-compose -f docker-compose_dev.yml up -d"           | ./boxes.sh ${LightCyan}
        windowBottom
        docker-compose -f docker-compose.yml run --service-ports pman_service
fi
