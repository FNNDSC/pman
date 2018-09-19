#!/usr/bin/env bash
#
# NAME
#
#   make
#
# SYNPOSIS
#
#   make
#
# DESC
# 
#   'make' sets up a pman instance using docker-compose.
#
# ARGS
#
#       


source ./decorate.sh 

declare -i STEP=0
declare -i b_restart=0
declare -i b_kill=0
JOB=""
HERE=$(pwd)
echo "Starting script in dir $HERE"

declare -a A_CONTAINER=(
    "pman${TAG}"
)

CREPO=fnndsc
TAG=

if [[ -f .env ]] ; then
    source .env 
fi

while getopts "k:r:psidUIa:S:" opt; do
    case $opt in 
        r) b_restart=1
           JOB=$OPTARG                          ;;
        k) b_kill=1
           JOB=$OPTARG                          ;;
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

title -d 1 "Setting global exports..."
    if (( ! b_storeBaseOverride )) ; then
        if [[ ! -d FS/remote ]] ; then
            mkdir -p FS/remote
        fi
        cd FS/remote
        STOREBASE=$(pwd)
        cd $HERE
    fi
    echo -e "${STEP}.1 For pman override to swarm containers, exporting\n\tSTOREBASE=$STOREBASE... "
    export STOREBASE=$STOREBASE
    if (( b_debug )) ; then
        echo -e "${STEP}.2 Setting debug quiet to OFF. Note this is noisy!"
        export CHRIS_DEBUG_QUIET=0
    fi
windowBottom

if (( b_restart || b_kill )) ; then
    printf "${Red}Stopping $JOB...${NC}\n"
    docker-compose stop ${JOB}_service && docker-compose rm -f ${JOB}_service
    if (( b_restart )) ; then
        printf "${Yellow}Restarting $JOB...${NC}\n"
        docker-compose run --service-ports ${JOB}_service
    fi
else
    title -d 1 "Using <$CREPO> family containers..."
    if (( ! b_skipIntro )) ; then 
        if [[ $CREPO == "fnndsc" ]] ; then
            echo "Pulling latest version of all containers..."
            for CONTAINER in ${A_CONTAINER[@]} ; do
                echo ""
                CMD="docker pull ${CREPO}/$CONTAINER"
                echo -e "\t\t\t${White}$CMD${NC}"
                echo $sep
                echo $CMD | sh
                echo $sep
            done
        fi
    fi
    windowBottom

    if (( ! b_skipIntro )) ; then 
        title -d 1 "Will use containers with following version info:"
        for CONTAINER in ${A_CONTAINER[@]} ; do
                CMD="docker run ${CREPO}/$CONTAINER --version"
                printf "${White}%40s\t\t" "${CREPO}/$CONTAINER"
                Ver=$(echo $CMD | sh | grep Version)
                echo -e "$Green$Ver"
        done
        windowBottom
    fi

    title -d 1 "Shutting down any running pman and pman related containers... "
    docker-compose stop
    docker-compose rm -vf
    for CONTAINER in ${A_CONTAINER[@]} ; do
        printf "%30s" "$CONTAINER"
        docker ps -a                                                        |\
            grep $CONTAINER                                                 |\
            awk '{printf("docker stop %s && docker rm -vf %s\n", $1, $1);}' |\
            sh >/dev/null
        printf "${Green}%20s${NC}\n" "done"
    done
    windowBottom

    cd $HERE
    title -d 1 "Changing permissions to 755 on" " $(pwd)"
    echo "chmod -R 755 $(pwd)"
    chmod -R 755 $(pwd)
    windowBottom

    title -d 1 "Creating tmp dirs for volume mounting into containers..."
    echo "${STEP}.1: Remove tree root 'FS'.."
    rm -fr ./FS 
    echo "${STEP}.2: Create tree structure for remote services in host filesystem..."
    mkdir -p FS/local
    chmod 777 FS/local
    mkdir -p FS/remote
    chmod 777 FS/remote
    mkdir -p FS/data 
    chmod 777 FS/data
    chmod 777 FS
    b_FSOK=1
    type -all tree >/dev/null 2>/dev/null
    if (( ! $? )) ; then
        tree FS
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
        printf "\n${Red}There should only be 3 directories and no files in the FS tree!\n"
        printf "${Yellow}Please manually clean/delete the entire FS tree and re-run.\n"
        printf "${Yellow}\nThis script will now exit with code '1'.\n\n"
        exit 1
    fi
    windowBottom


    title -d 1 "Starting pman containerized development environment using " " ./docker-compose.yml"
    # echo "docker-compose up -d"
    # docker-compose up -d
        docker-compose run --service-ports pman_service
    windowBottom

    # title -d 1 "Pause for manual restart of services?"
    # if (( b_pause )) ; then
    #     read -n 1 -p "Hit ANY key to continue..." anykey
    #     echo ""
    # fi
    # windowBottom

    # if (( !  b_norestartinteractive_chris_dev )) ; then
    #     title -d 1 "Restarting pman development container in interactive mode..."
    #     docker-compose stop pman_service
    #     docker-compose rm -f pman_service
    #     docker-compose run --service-ports pman_service
    #     echo ""
    #     windowBottom
    # fi
fi
