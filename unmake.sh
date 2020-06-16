#!/bin/bash

source ./decorate.sh

declare -i STEP=0

title -d 1 "Destroying containerized development environment" \
                "from  ./docker-compose.yml"
    echo "Do you want to stop and rm all containers? [y/n]"                 | ./boxes.sh
    windowBottom
    old_stty_cfg=$(stty -g)
    stty raw -echo ; REPLY=$(head -c 1) ; stty $old_stty_cfg
    echo -en "\033[2A\033[2K"
    windowBottom
    if [[ $REPLY =~ ^[Yy]$ ]] ; then

        title -d 1 "Stopping services..."
            echo "This might take a few minutes... please be patient."      | ./boxes.sh ${Yellow}
            windowBottom
            docker-compose --no-ansi stop >& dc.out
            echo -en "\033[2A\033[2K"
            cat dc.out | sed -E 's/(.{80})/\1\n/g'                          | ./boxes.sh ${LightBlue}
        windowBottom

        title -d 1 "Removing all containers..."
            echo "This might take a few minutes... please be patient."      | ./boxes.sh ${Yellow}
            windowBottom
            docker-compose --no-ansi rm -vf >& dc.out
            echo -en "\033[2A\033[2K"
            cat dc.out | sed -E 's/(.{80})/\1\n/g'                          | ./boxes.sh ${LightBlue}
        windowBottom

        title -d 1 "Removing any orphans..."
            a_VOLS=(
                "pman"
            )
            a_PVOLS=()
            for vol in ${a_VOLS[@]}; do
                DOCKERPS=$(docker ps -a | grep -v CONTAINER | grep $vol)
                DOCKERVOLNAME=$(echo $DOCKERPS | awk '{print $2}')
                DOCKERID=$(echo $DOCKERPS | awk '{print $1}')
                if (( ${#DOCKERVOLNAME} )); then
                    printf "%50s${Yellow}%30s${NC}\n"   \
                        "Scanning for $vol... "         \
                        "[ $DOCKERID:$DOCKERVOLNAME ]"                      | boxes.sh
                else
                    printf "%50s${Green}%30s${NC}\n"    \
                        "Scanning for $vol... " "[ Not orphaned. ]"         | boxes.sh
                fi
                a_PVOLS+=($DOCKERID)
            done
            echo ""                                                         | boxes.sh
            for VOL in ${a_PVOLS[@]} ; do
                printf "${Cyan}%50s${Yellow}%30s${NC}\n"    \
                        "Removing" " [ $VOL ]"                              | boxes.sh
                docker stop $VOL   > dc.out
                cat dc.out                                                  | boxes.sh
                docker rm -vf $VOL > dc.out
                cat dc.out                                                  | boxes.sh
            done
        windowBottom

        title -d 1 "Quick filesystem ops..."
        echo "Removing ./FS tree"                                           | ./boxes.sh
        rm -fr ./FS
    else
        printf "Keeping all containers intact...\n"                         | ./boxes.sh ${LightGreen}
        windowBottom
        echo -en "\033[2A\033[2K"
    fi
windowBottom

