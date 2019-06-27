FROM fnndsc/ubuntu-python3:latest
MAINTAINER fnndsc "dev@babymri.org"

ARG UID=1001
ENV UID=$UID





COPY ./docker-entrypoint.py /dock/docker-entrypoint.py
COPY ./run.sh /dock/run.sh
COPY ./recip.txt /dock/recip.txt
COPY ./setup.sh /dock/setup.sh


RUN apt-get update \
  && apt-get install sudo                                             \
  && useradd -u $UID -ms /bin/bash localuser                          \
  && addgroup localuser sudo                                          \
  && echo "localuser:localuser" | chpasswd                            \
  && adduser localuser sudo               \  
  && apt-get install -y libssl-dev libcurl4-openssl-dev bsdmainutils vim net-tools inetutils-ping \
    && sudo pip3 install pfurl                                          


RUN chmod 777 /dock                                                   \
  && chmod 777 /dock/run.sh \
    && chmod 777 /dock/docker-entrypoint.py \
    && chmod 777 /dock/recip.txt \
&& chmod 777 /dock/setup.sh \
  && echo "localuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

RUN rm /bin/sh && ln -s /bin/bash /bin/sh

# Set Arguments here
ARG Email="redhathttptester@gmail.com"
ARG Password="Yosoyunprogramo"
ARG Body="There is an error in accessing the MOC website"
ARG Subject="Http Error in MOC server"
ARG ErrorCount="5"
ARG Iterations="10"
ARG Wait="5"
ARG HostUrl="pman-radiology.k-apps.osh.massopen.cloud"

ENV email=$Email
ENV password=$Password
ENV body=$Body
ENV subject=$Subject
ENV errorcount=$ErrorCount
ENV iterations=$Iterations
ENV wait=$Wait
ENV hosturl=$HostUrl



ENTRYPOINT ["/dock/docker-entrypoint.py"]

# Start as user $UID
USER $UID
