#!/usr/bin/env bash
sudo apt-get remove docker docker-engine docker.io

sudo apt-get update
sudo apt-get install linux-image-extra-$(uname -r) linux-image-extra-virtual
sudo apt-get install apt-transport-https ca-certificates curl software-properties-common

#Add Docker’s official GPG key
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

#Add stable repository
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

#Install docker ce
sudo apt-get update
sudo apt-cache policy
sudo apt-get install -y docker-ce

#Check if docker runs as non root
docker -v
sudo cat /etc/docker/daemon.json
sudo sed -i 's/}/,"insecure-registries":["172.30.0.0\/16\"]}/' /etc/docker/daemon.json
sudo cat /etc/docker/daemon.json
sudo systemctl restart docker
docker info 

#Install Docker Compose 
sudo curl -L https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-`uname -s`-`uname -m` > docker-compose
sudo chmod +x docker-compose
sudo mv docker-compose /usr/local/bin

#Test Docker and Docker Compose version
echo 'Test Docker and Docker Compose version'
echo '______________________________________'
docker -v
docker-compose -v

# Install oc cluster 
# This script assumes Docker is already installed

set -x

# Download and install the oc binary
sudo mount --make-shared /
wget https://github.com/openshift/origin/releases/download/v$OPENSHIFT_VERSION/openshift-origin-client-tools-v$OPENSHIFT_VERSION-$OPENSHIFT_COMMIT-linux-64bit.tar.gz
tar xvzOf openshift-origin-client-tools-v$OPENSHIFT_VERSION-$OPENSHIFT_COMMIT-linux-64bit.tar.gz > oc.bin
sudo mv oc.bin /usr/local/bin/oc
sudo chmod 755 /usr/local/bin/oc

# Figure out this host's IP address
IP_ADDR="$(ip addr show eth0 | grep "inet\b" | awk '{print $2}' | cut -d/ -f1)"

# Start OpenShift
oc cluster up --public-hostname=$IP_ADDR
oc login -u system:admin

# Wait until we have a ready node in openshift
TIMEOUT=0
TIMEOUT_COUNT=60
until [ $TIMEOUT -eq $TIMEOUT_COUNT ]; do
  if [ -n "$(oc get nodes | grep Ready)" ]; then
    break
  fi

  echo "openshift is not up yet"
  let TIMEOUT=TIMEOUT+1
  sleep 5
done

if [ $TIMEOUT -eq $TIMEOUT_COUNT ]; then
  echo "Failed to start openshift"
  exit 1
fi