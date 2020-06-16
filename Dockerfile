#
# Dockerfile for pman repository.
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
ENV UID=$UID DEBIAN_FRONTEND=noninteractive

COPY . /tmp/pman
COPY ./docker-entrypoint.py /dock/docker-entrypoint.py

RUN export LC_ALL=en_US.UTF-8                                         \
  && export LANG=en_US.UTF-8                                          \
  && pip install --upgrade pip                                        \
  && apt-get update                                                   \
  && apt-get install locales && locale-gen en_US.UTF-8                \
  && apt-get install sudo                                             \
  && useradd -u $UID -ms /bin/bash localuser                          \
  && addgroup localuser sudo                                          \
  && echo "localuser:localuser" | chpasswd                            \
  && adduser localuser sudo                                           \
  && apt-get install -y libssl-dev libcurl4-openssl-dev bsdmainutils net-tools inetutils-ping \
  && pip install --upgrade pip                                        \
  && pip3 install /tmp/pman                                           \
  && rm -rf /tmp/pman                                                 \
  && chmod 777 /dock                                                  \
  && chmod 777 /dock/docker-entrypoint.py                             \
  && echo "localuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

ENTRYPOINT ["/dock/docker-entrypoint.py"]
EXPOSE 5010

# Start as user $UID
# USER $UID
