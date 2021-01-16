#
# Dockerfile for pman production.
#
# Build with
#
#   docker build -t <name> .
#
# For example if building a local version, you could do:
#
#   docker build -t local/pman .
#
# In the case of a proxy (located at say 10.41.13.4:3128), do:
#
#    export PROXY="http://10.41.13.4:3128"
#    docker build --build-arg http_proxy=${PROXY} --build-arg UID=$UID -t local/pman .
#
# To run an interactive shell inside this container, do:
#
#   docker run -ti --rm --entrypoint /bin/bash local/pman
#
# To pass an env var HOST_IP to container, do:
#
#   docker run -ti --rm -e HOST_IP=$(ip route | grep -v docker | awk '{if(NF==11) print $9}') --entrypoint /bin/bash local/pman
#

FROM fnndsc/ubuntu-python3:latest
LABEL maintainer="dev@babymri.org"

# Pass a UID on build command line (see above) to set internal UID
ARG UID=1001
ENV UID=$UID DEBIAN_FRONTEND=noninteractive APPROOT="/home/localuser/pman"

RUN apt-get update                                                \
  && apt-get install -y locales                                   \
  && export LANGUAGE=en_US.UTF-8                                  \
  && export LANG=en_US.UTF-8                                      \
  && export LC_ALL=en_US.UTF-8                                    \
  && locale-gen en_US.UTF-8                                       \
  && dpkg-reconfigure locales                                     \
  && apt-get install -y libssl-dev libcurl4-openssl-dev bsdmainutils net-tools inetutils-ping \
  && pip install --upgrade pip                                        \
  && useradd -u $UID -ms /bin/bash localuser

# Copy source code
COPY --chown=localuser ./bin ${APPROOT}/bin
COPY --chown=localuser ./docker-bin ${APPROOT}/docker-bin
COPY --chown=localuser ./pman ${APPROOT}/pman
COPY --chown=localuser ./openshift ${APPROOT}/openshift
COPY --chown=localuser ./setup.cfg ./setup.py README.rst  ${APPROOT}/

RUN pip3 install ${APPROOT}  \
  && rm -fr ${APPROOT}

# Start as user localuser
#USER localuser

WORKDIR "/home/localuser"

COPY --chown=localuser ./docker-entrypoint.sh /home/localuser/docker-entrypoint.sh
ENTRYPOINT ["/home/localuser/docker-entrypoint.sh"]
EXPOSE 5010
