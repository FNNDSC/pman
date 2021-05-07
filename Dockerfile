#
# Docker file for pman image
#
# Build production image:
#
#   docker build -t <name> .
#
# For example if building a local production image:
#
#   docker build -t local/pman .
#
# Build development image:
#
#   docker build --build-arg ENVIRONMENT=local -t <name>:<tag> .
#
# For example if building a local development image:
#
#   docker build --build-arg ENVIRONMENT=local -t local/pman:dev .
#
# In the case of a proxy (located at say proxy.tch.harvard.edu:3128), do:
#
#    export PROXY="http://proxy.tch.harvard.edu:3128"
#
# then add to any of the previous build commands:
#
#    --build-arg http_proxy=${PROXY}
#
# For example if building a local development image:
#
# docker build --build-arg http_proxy=${PROXY} --build-arg ENVIRONMENT=local -t local/pman:dev .
#

FROM fnndsc/ubuntu-python3:ubuntu20.04-python3.8.5
MAINTAINER fnndsc "dev@babymri.org"

# Pass a UID on build command line (see above) to set internal UID
ARG UID=1001
ARG ENVIRONMENT=production

ENV UID=$UID DEBIAN_FRONTEND=noninteractive VERSION="0.1"
ENV APPROOT="/home/localuser/pman" REQPATH="/usr/src/requirements"

RUN apt-get update                                                                       \
  && apt-get install -y locales                                                          \
  && export LANGUAGE=en_US.UTF-8                                                         \
  && export LANG=en_US.UTF-8                                                             \
  && export LC_ALL=en_US.UTF-8                                                           \
  && locale-gen en_US.UTF-8                                                              \
  && dpkg-reconfigure locales                                                            \
  && apt-get install -y gunicorn                                                         \
  && useradd -u $UID -ms /bin/bash localuser

COPY ["./requirements", "${REQPATH}"]

# Copy source code and make localuser the owner
COPY --chown=localuser ./bin ${APPROOT}/bin
COPY --chown=localuser ./pman ${APPROOT}/pman
COPY --chown=localuser ./setup.cfg ./setup.py README.rst ${APPROOT}/

RUN pip install --upgrade pip                                                            \
  && pip install -r ${REQPATH}/${ENVIRONMENT}.txt

# Start as user localuser
#USER localuser

WORKDIR ${APPROOT}
ENTRYPOINT []
EXPOSE 5010

# Start pman production server
CMD ["gunicorn", "-w", "5", "-b", "0.0.0.0:5010", "pman.wsgi:application"]
