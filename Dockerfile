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

FROM fnndsc/ubuntu-python3:ubuntu20.04-python3.8.5
MAINTAINER fnndsc "dev@babymri.org"

# Pass a UID on build command line (see above) to set internal UID
ARG UID=1001
ENV UID=$UID DEBIAN_FRONTEND=noninteractive APPLICATION_MODE="production" APPROOT="/home/localuser/pman"

RUN apt-get update                                                                       \
  && apt-get install -y locales                                                          \
  && export LANGUAGE=en_US.UTF-8                                                         \
  && export LANG=en_US.UTF-8                                                             \
  && export LC_ALL=en_US.UTF-8                                                           \
  && locale-gen en_US.UTF-8                                                              \
  && dpkg-reconfigure locales                                                            \
  && apt-get install -y gunicorn                                                         \
  && pip install --upgrade pip                                                           \
  && useradd -u $UID -ms /bin/bash localuser

# Copy source code and make localuser the owner
COPY --chown=localuser ./bin ${APPROOT}/bin
COPY --chown=localuser ./pman ${APPROOT}/pman
COPY --chown=localuser ./setup.cfg ./setup.py README.rst ${APPROOT}/

RUN pip3 install ${APPROOT}

# Start as user localuser
#USER localuser

WORKDIR ${APPROOT}
ENTRYPOINT ["gunicorn"]
EXPOSE 5010

# Start pman production server
CMD ["-w", "5", "-b", "0.0.0.0:5010", "pman.wsgi:application"]
