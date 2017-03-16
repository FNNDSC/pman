#!/bin/bash

# Single entry point / dispatcher for simplified running of
#
## pman
## pfioh
## purl
#

G_SYNOPSIS="

 NAME

    docker-entrypoint.sh

 SYNOPSIS

    docker-entrypoint.sh    pman || pfioh || purl
                            [optional cmd args for each]


 DESCRIPTION

    'docker-entrypoint.sh' is the main entrypoint for running one of three applications
    contained within the fnndsc/pman docker container.

    Two of these, 'pman' and 'pfioh' are services, while the third 'purl' is a CLI app to
    communicate with these services.



"

function pman_do
{
    echo "in pman..."
    echo "len args = $#"
    echo $*
}

function pfioh_do
{
    echo "in pfioh..."
    echo $*
}

function purl_do
{
    echo "in purl..."
    CMD="/usr/local/bin/purl --verb POST --raw --http ${PMAN_PORT_5010_TCP_ADDR}:5010/api/v1/cmd --jsonwrapper 'payload' --msg '$*'"
    echo "$*"
    echo "$#"
    echo "$CMD"
}

# First, determine which app we are running:
APP=$1
echo $APP

# Now gather any optional arguments...
shift
ARGS="$*"

# And call the relevant dispatching function
FUNC=${APP}_do
eval $FUNC "$ARGS"
