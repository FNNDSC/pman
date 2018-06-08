#!/bin/bash
#
# NAME
#
#   decorate.sh
#
# DESC
#   Contains utility functions for the 'docker-make-chris_dev.sh' script.
#

   ESC(){ echo -en "\033";}                             # escape character
 CLEAR(){ echo -en "\033c";}                            # the same as 'tput clear'
 CIVIS(){ echo -en "\033[?25l";}                        # the same as 'tput civis'
 CNORM(){ echo -en "\033[?12l\033[?25h";}               # the same as 'tput cnorm'
  TPUT(){ echo -en "\033[${1};${2}H";}                  # the same as 'tput cup'
COLPUT(){ echo -en "\033[${1}G";}                       # put text in the same line as the specified column
  MARK(){ echo -en "\033[7m";}                          # the same as 'tput smso'
UNMARK(){ echo -en "\033[27m";}                         # the same as 'tput rmso'
  DRAW(){ echo -en "\033%@";echo -en "\033(0";}         # switch to 'garbage' mode
 # DRAW(){ echo -en "\033%";echo -en "\033(0";}          # switch to 'garbage' mode
 WRITE(){ echo -en "\033(B";}                           # return to normal mode from 'garbage' on the screen
  BLUE(){ echo -en "\033c\033[0;1m\033[37;44m\033[J";}  # reset screen, set background to blue and font to white

# Foreground
RED='\033[0;31m'
NC='\033[m' # No Color
Black='\033[0;30m'     
DarkGray='\033[1;30m'
Red='\033[0;31m'     
LightRed='\033[1;31m'
Green='\033[0;32m'     
LightGreen='\033[1;32m'
Brown='\033[0;33m'     
Yellow='\033[1;33m'
Blue='\033[0;34m'     
LightBlue='\033[1;34m'
Purple='\033[0;35m'     
LightPurple='\033[1;35m'
Cyan='\033[0;36m'     
LightCyan='\033[1;36m'
LightGray='\033[0;37m'     
White='\033[1;37m'

# Background
NC='\033[m' # No Color
BlackBG='\033[0;40m'     
DarkGrayBG='\033[1;40m'
RedBG='\033[0;41m'     
LightRedBG='\033[1;41m'
GreenBG='\033[0;42m'     
LightGreenBG='\033[1;42m'
BrownBG='\033[0;43m'     
YellowBG='\033[1;43m'
BlueBG='\033[0;44m'     
LightBlueBG='\033[1;44m'
PurpleBG='\033[0;45m'     
LightPurpleBG='\033[1;45m'
CyanBG='\033[0;46m'     
LightCyanBG='\033[1;46m'
LightGrayBG='\033[0;47m'     
WhiteBG='\033[1;47m'

function title {
    declare -i b_date=0
    local OPTIND
    while getopts "d:" opt; do
        case $opt in 
            d) b_date=$OPTARG ;;
        esac
    done
    shift $(($OPTIND - 1))

    STEP=$(expr $STEP + 1 )
    MSG="$1"
    MSG2="$2"
    TITLE=$(echo " $STEP: $MSG ")
    LEN=$(echo "$TITLE" | awk -F\| {'printf("%s", length($1));'})
    if ! (( LEN % 2 )) ; then
        TITLE="$TITLE "
    fi
    MSG=$(echo -e "$TITLE" | awk -F\| {'printf("%*s%*s\n", 40+length($1)/2, $1, 41-length($1)/2, "");'})
    if (( ${#MSG2} )) ; then
        TITLE2=$(echo " $MSG2 ")
        LEN2=$(echo "$TITLE2" | awk -F\| {'printf("%s", length($1));'})
        MSG2=$(echo -e "$TITLE2" | awk -F\| {'printf("%*s%*s\n", 40+length($1)/2, $1, 41-length($1)/2, "");'})
    fi
    printf "\n"
    DATE=" $(date) [$(hostname)] "
    lDATE=${#DATE}
    DRAW
    if (( b_date )) ; then
        printf "${LightBlue}l" ;  for c in $(seq 1 $lDATE); do printf "q" ; done ; 
        printf "k\nx"
        WRITE
        printf "%-30s" "$DATE"
        DRAW 
        printf "x\n"
        printf "${Yellow}t" ; for c in $(seq 1 $lDATE); do printf "q";  done ; printf "v"
        REM=$(expr 79 - $lDATE)
        for c in $(seq 1 $REM); do printf "q" ; done ; printf "k\n"
    else
        printf "${Yellow}l"
        for c in $(seq 1 80); do printf "q" ; done
        printf "k\n"
    fi
    printf "x"
    WRITE
    printf "${LightPurple}$MSG${Yellow}"
    if (( ${#MSG2} )) ; then
        DRAW
        printf "x\nx"
        WRITE
        printf "${LightPurple}$MSG2${Yellow}"
    fi
    DRAW
    printf "x\n"
    printf "${Yellow}t" ;  for c in $(seq 1 80); do printf "q" ; done ; printf "u\n"
    WRITE
    printf "${NC}"
}

function windowBottom {
    # printf "a b c d f e f g h i j k l m n o p q r s t u v w x y z]\n"
    DRAW
    # printf "a b c d f e f g h i j k l m n o p q r s t u v w x y z]\n"
    printf "${Yellow}mw" ;  for c in $(seq 1 79); do printf "q" ; done ; printf "v${Brown}qk\n"
    # printf "mwqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqv${Brown}qk\n"
    # printf "mqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqj\n"
    printf "${Brown} m" ; for c in $(seq 1 81); do printf "q" ; done ; printf "j\n"
    # printf " mqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqj\n"
    WRITE
    printf "${NC}"
}
