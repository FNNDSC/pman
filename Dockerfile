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
#    docker build --build-arg http_proxy=http://192.168.13.14:3128 -t local/pman .
#

FROM fnndsc/ubuntu-python3:latest
MAINTAINER fnndsc "dev@babymri.org"

RUN apt-get update \
  && apt-get install -y libssl-dev libcurl4-openssl-dev bsdmainutils  \
  && pip3 install pudb                                                \
  && pip3 install pyzmq                                               \
  && pip3 install webob                                               \
  && pip3 install psutil                                              \
  && pip3 install pman==1.3.1                                         \ 
  && pip3 install docker                                              \
  && pip3 install kubernetes                                          \
  && pip3 install openshift

COPY ./docker-entrypoint.py /dock/docker-entrypoint.py
RUN chmod 777 /dock && chmod 777 /dock/docker-entrypoint.py
ENTRYPOINT ["/dock/docker-entrypoint.py"]
USER 1001
EXPOSE 5010
