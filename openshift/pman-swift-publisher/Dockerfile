#
# Dockerfile for the pman-swift-publisher image.
#
# Build with
#
#   docker build -t <name> .
#
# For example if building a local version, you could do:
#
#   docker build -t local/pman-swift-publisher .
#

FROM fnndsc/ubuntu-python3:latest
MAINTAINER fnndsc "dev@babymri.org"

RUN apt-get update \
    && apt-get install -y curl \
    && pip3 install --upgrade pip \
    && pip3 install python-keystoneclient \ 
    && pip3 install python-swiftclient \
    && pip3 install kubernetes \
    && pip3 install fasteners


ARG APPROOT="/usr/src/pman-swift-publisher"  
ARG VERSION="0.1"
COPY ["get_data.py", "put_data.py", "swift_handler.py", "${APPROOT}/"]

WORKDIR $APPROOT
