#!/usr/bin/env bash
sudo oc login -u system:admin
sudo oc create sa robot -n myproject
token=$(sudo oc describe sa robot -n myproject | grep 'Tokens: *' | grep -o 'robot-token-.....')
sudo oc adm policy add-role-to-user edit system:serviceaccount:myproject:robot -n myproject
sudo oc describe secret $token -n myproject

mkdir /tmp/share
chcon -R -t svirt_sandbox_file_t /tmp/share/
sudo oc edit scc restricted
