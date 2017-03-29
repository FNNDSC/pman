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
  && apt-get install -y libssl-dev libcurl4-openssl-dev bsdmainutils \
  && pip3 install pman==0.12.7 \
  && mkdir /entrypoint \
  && chown -R 1001:0 /entrypoint

COPY ./docker-entrypoint.py /entrypoint/docker-entrypoint.py

RUN chmod -R ug+rwx /entrypoint

USER 1001

ENTRYPOINT ["/entrypoint/docker-entrypoint.py"]
EXPOSE 5010 5055
