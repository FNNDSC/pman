#
# Dockerfile for the pman-reaper image.
#
# Build with
#
#   docker build -t <name> .
#
# For example if building a local version, you could do:
#
#   docker build -t local/pman-reaper .
#

FROM fnndsc/ubuntu-python3:latest
MAINTAINER fnndsc "dev@babymri.org"

RUN apt-get update \
    && pip3 install kubernetes


ARG APPROOT="/usr/src/openshift-pman-reaper"  
ARG VERSION="0.1"
COPY ["reaper.py", "${APPROOT}/"]

WORKDIR $APPROOT
