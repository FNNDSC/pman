#!/usr/bin/env bash

set -ev
cd ..
git clone https://github.com/FNNDSC/ChRIS_ultron_backEnd.git
pushd pman/
docker build -t fnndsc/pman:latest .
oc new-app openshift/pman-openshift-template-without-swift.json

# Deploy pfioh to OpenShift. We can directly pull the container but just for sake of being in sync with other repos and
# making our debugging easier.
popd
git clone https://github.com/FNNDSC/pfioh.git
pushd pfioh/
docker build -t fnndsc/pfioh:latest .
oc new-app openshift/pfioh-openshift-template-without-swift.json

sleep 10 # Wait for deployments to run.

# Deploy pfcon. 
# TODO: Change this to deploying on OpenShift using environment variables
popd
git clone https://github.com/FNNDSC/pfcon.git
pushd pfcon/
# Update pman and pfioh from routes
export pman_route=`oc get routes | awk '{print $2}'| grep pman`
export pfioh_route=`oc get routes | awk '{print $2}'| grep pfioh`
sed -i 's/127.0.0.1:5010/${pman_route}/g' pfcon/pfcon.py
sed -i 's/%PMAN_IP:5010/${pman_route}/g' pfcon/pfcon.py
sed -i 's/%PFIOH_IP:5055/${pfioh_route}/g' pfcon/pfcon.py
sed -i 's/127.0.0.1:5055/${pfioh_route}/g' pfcon/pfcon.py
docker build -t fnndsc/pfcon:latest .

popd
pushd ChRIS_ultron_backEnd/
docker build -t fnndsc/chris:dev -f Dockerfile_dev .
docker pull fnndsc/pfdcm
docker pull fnndsc/swarm
docker swarm init --advertise-addr 127.0.0.1
chmod -R 755 $(pwd)
mkdir -p FS/remote
chmod -R 777 FS
export STOREBASE=$(pwd)/FS/remote
docker-compose -f docker-compose_dev.yml up -d
docker-compose -f docker-compose_dev.yml exec chris_dev_db sh -c 'while ! mysqladmin -uroot -prootp status 2> /dev/null; do sleep 5; done;'
docker-compose -f docker-compose_dev.yml exec chris_dev_db mysql -uroot -prootp -e 'GRANT ALL PRIVILEGES ON *.* TO "chris"@"%"'
