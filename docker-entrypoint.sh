#!/bin/bash

sudo chown localuser:localuser /var/run/docker.sock

exec "$@"