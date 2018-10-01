#!/usr/bin/env bash
set -ev
cd ..
git clone https://github.com/FNNDSC/ChRIS_ultron_backEnd.git
pushd pman/
docker build -t fnndsc/pman:latest .
# add ravig's pfcon for testing with pman & pfioh from openshift hosted on moc
docker pull ravig/pfcon:latest
docker tag ravig/pfcon fnndsc/pfcon:latest
popd
pushd ChRIS_ultron_backEnd/
docker build -t fnndsc/chris_dev_backend .
export STOREBASE=$(pwd)/FS/remote
docker-compose up -d
docker-compose exec chris_dev_db sh -c 'while ! mysqladmin -uroot -prootp status 2> /dev/null; do sleep 5; done;'
docker-compose exec chris_dev_db mysql -uroot -prootp -e 'GRANT ALL PRIVILEGES ON *.* TO "chris"@"%"'
docker-compose exec chris_dev python manage.py migrate
docker swarm init --advertise-addr 127.0.0.1
