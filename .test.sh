#!/bin/bash
rep=$(curl -s --unix-socket /var/run/docker.sock http://ping > /dev/null)
status=$?

if [ "$status" == "7" ]; then
    sudo systemctl restart docker
fi