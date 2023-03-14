#!/bin/bash -e
# Test pman in isolation with docker OR podman
#
# Notes:
# - state is dirty if tests fail
# - suggested that you run this script with no existing containers nor volumes

set -o pipefail

HERE=$(dirname "$(readlink -f "$0")")

CONTAINER_RUNTIME=$1

if [ -z "$CONTAINER_RUNTIME" ]; then
  echo "usage: $0 [docker|podman]"
  exit 1
fi

CR_EXEC=$(which $CONTAINER_RUNTIME)

# shadows the name "podman" so that it calls the specified runtime
# which might be docker OR podman
function podman () {
  $CR_EXEC "$@"
}

# find out where the podman/docker socket is
if [ -n "$DOCKER_HOST" ]; then
  socket="$DOCKER_HOST"
else
  if [[ "$CR_EXEC" = *podman* ]]; then
    if [ "$(podman info --format '{{ .Host.RemoteSocket.Exists }}')" != 'true' ]; then
      echo "error: podman socket must be active."
      echo "try running:"
      echo
      echo "    systemctl --user start podman.service"
      echo
      exit 1
    fi
    socket="$(podman info --format '{{ .Host.RemoteSocket.Path }}')"
  elif [[ "$CR_EXEC" = *docker* ]]; then
    socket=/var/run/docker.sock
  fi
fi

set -ex

# pull example ChRIS plugin
SIMPLEDSAPP=docker.io/fnndsc/pl-simpledsapp:2.1.0
podman pull $SIMPLEDSAPP

# build
pman_image="localhost/fnndsc/pman:${0##*/}"
podman build -t $pman_image .

# "storebase" directory where "pfcon" writes data
volume=$(podman volume create --driver local)
storeBase=$(podman volume inspect --format '{{ .Mountpoint }}' $volume)

# simulate action of pfcon receiving data
jid="pmantest-$RANDOM"

podman run --rm \
  -v "$HERE:/here:ro" -w /here \
  -v "$volume:/var/local/storeBase:rw"  \
  alpine sh -c "mkdir -vp /var/local/storeBase/key-$jid/incoming /var/local/storeBase/key-$jid/outgoing && cp -v README.md LICENSE /var/local/storeBase/key-$jid/incoming"

# pman identifies the aforementioned volume by inspecting
# its peer pfcon, so run a mock pfcon container
mock_pfcon=$(podman run -d -v "$volume:/var/local/storeBase" -l org.chrisproject.role=pfcon alpine sleep 60)

# run pman in the background

# IGNORE_LIMITS is forwarded to the container as a workaround for a Github Actions bug,
# see .github/workflows/ci.yml

pman=$(
  podman run -d --userns host -p 5010:5010 \
    -e IGNORE_LIMITS \
    -v $socket:/var/run/docker.sock:rw \
    -e SECRET_KEY=secret -e CONTAINER_ENV=$CONTAINER_RUNTIME \
    $pman_image
)

# wait for pman to be up
set +e
elapsed=0
until [ "$(curl -w '%{http_code}' -o /dev/null -s --head http://localhost:5010/api/v1/)" = "200" ]; do
  sleep 1
  if [  "$((elapsed++))" -gt "5" ]; then
    echo "error: timed out waiting for pman"
    exit 1
  fi
done

# submit job to pman
set -e
body="$(cat << EOF
{
  "jid": "$jid",
  "args": [
    "--saveinputmeta", "--saveoutputmeta",
    "--prefix", "hello_test_"
  ],
  "auid": "cube-test",
  "number_of_workers": "1",
  "cpu_limit": "1000",
  "memory_limit": "200",
  "gpu_limit": "0",
  "image": "$SIMPLEDSAPP",
  "entrypoint": ["simpledsapp"],
  "type": "ds"
}
EOF
)"

curl -H 'Accept: application/json' -H 'Content-Type: application/json' \
  --data "$body" -s http://localhost:5010/api/v1/

podman logs $pman  # debug output

# assert pman created container, and that STOREBASE was mounted
podman container inspect --format '{{ range .Mounts }}{{ .Source }}{{end}}' $jid \
  | grep -Fqm 1 "$storeBase/key-$jid"

# wait for simpledsapp to finish
rc=$(podman wait $jid)
if [ "$rc" != "0" ]; then
  echo "failed assertion: $jid exited with code $rc"
  exit $rc
fi

podman logs $jid  # debug output

# assert simpledsapp worked
podman run --rm -v "$storeBase/key-$jid:/share:ro" alpine diff -rq \
  "/share/incoming/README.md" \
  "/share/outgoing/hello_test_README.md"

# assert pman reports simpledsapp finishedSuccessfully
status="$(curl -sH 'Accept: application/json' http://localhost:5010/api/v1/$jid/ | jq -r '.status')"

if [ "$status" != "finishedSuccessfully" ]; then
  echo "failed assertion: pman reports $jid has status \"$status\""
  exit 1
fi

# delete job
set +e
curl -sX DELETE http://localhost:5010/api/v1/$jid/
set +o pipefail
podman container inspect $jid 2>&1 | grep -Fqm 1 "no such container" \
  || (echo "assertion failed: container $jid not deleted"; exit 1)

set +x

cat << EOF

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!                            !!
!!        TESTS PASSED        !!
!!                            !!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

EOF

# clean up
set -ex
podman kill $pman $mock_pfcon
podman rm $pman $mock_pfcon
podman volume rm $volume
# podman rmi $pman_image  # optional
