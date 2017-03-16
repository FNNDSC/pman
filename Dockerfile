# Docker file for pman server

FROM fnndsc/ubuntu-python3:latest
MAINTAINER fnndsc "dev@babymri.org"

RUN apt-get update \
  && apt-get install -y libssl-dev libcurl4-openssl-dev \
  && pip3 install pman==0.11.3

COPY ./docker-entrypoint.py /root/docker-entrypoint.py
ENTRYPOINT ["/root/docker-entrypoint.py"]
EXPOSE 5010 5055
