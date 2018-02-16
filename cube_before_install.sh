#!/bin/bash
sudo apt-get remove docker docker-engine docker.io
sudo apt-get update
sudo apt-get install linux-image-extra-$(uname -r) linux-image-extra-virtual
sudo apt-get install apt-transport-https ca-certificates curl software-properties-common
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-cache madison docker-ce
sudo apt-get install docker-ce=${DOCKER_VERSION}
 # update docker compose
sudo curl -L https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-`uname -s`-`uname -m` > docker-compose
sudo chmod +x docker-compose
sudo mv docker-compose /usr/local/bin
docker -v
docker-compose -v