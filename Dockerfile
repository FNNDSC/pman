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
# In the case of a proxy (located at 192.168.13.14:3128), do:
#
#    docker build --build-arg http_proxy=http://192.168.13.14:3128 --build-arg UID=$UID -t local/pman .
#
# To run an interactive shell inside this container, do:
#
#   docker run -ti --entrypoint /bin/bash local/pman
#

FROM fnndsc/ubuntu-python3:latest
MAINTAINER fnndsc "dev@babymri.org"

ARG UID=1001
ENV UID=$UID

RUN apt-get update                                                    \
  && apt-get install sudo                                             \
  && useradd -u $UID -ms /bin/bash localuser                          \
  && addgroup localuser sudo                                          \
  && echo "localuser:localuser" | chpasswd                            \
  && adduser localuser sudo                                           \
  && apt-get update                                                   \
  && apt-get install -y libssl-dev libcurl4-openssl-dev bsdmainutils net-tools inetutils-ping \
  && pip3 install pudb                                                \
  && pip3 install pyzmq                                               \
  && pip3 install webob                                               \
  && pip3 install psutil                                              \
  && pip3 install pman==1.4.0                                         \ 
  && pip3 install docker                                              \
  && pip3 install kubernetes                                          \
  && pip3 install openshift

COPY ./docker-entrypoint.py /dock/docker-entrypoint.py
RUN chmod 777 /dock && chmod 777 /dock/docker-entrypoint.py
RUN echo "localuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
ENTRYPOINT ["/dock/docker-entrypoint.py"]
USER $UID
EXPOSE 5010
