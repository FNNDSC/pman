#!/bin/bash

chown localuser:localuser /var/run/docker.sock

exec "$@"