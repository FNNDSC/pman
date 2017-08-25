#!/bin/bash

TOKEN="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)"
while true; do
  curl --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt     "https://openshift.default.svc.cluster.local/api/v1/namespaces/radiology/pods/$HOSTNAME"     -H "Authorization: Bearer $TOKEN" | python3 status.py
  if [ $? -eq 0 ]
  then
    python3 put_data.py
    break
  else
    sleep 10
  fi
done
