#############
pman v3.0.0.0
#############

.. image:: https://img.shields.io/docker/v/fnndsc/pman?sort=semver
    :alt: Docker Image Version
    :target: https://hub.docker.com/r/fnndsc/pman
.. image:: https://img.shields.io/github/license/fnndsc/pfioh
    :alt: MIT License
    :target: https://github.com/FNNDSC/pman/blob/master/LICENSE
.. image:: https://github.com/FNNDSC/pman/workflows/ci/badge.svg
    :alt: Github Actions
    :target: https://github.com/FNNDSC/pman/actions

.. contents:: Table of Contents

********
Overview
********

This repository proves ``pman`` -- a process manager.
``pman`` provides a unified API over HTTP for running jobs on

* docker swarm
* OpenShift

For more info see
https://github.com/FNNDSC/pman/wiki/pman-overview

***********
Basic Usage
***********

The most common use case for ``pman`` is for running jobs against *docker swarm*.

Installation
============

.. code-block:: bash

    docker pull fnndsc/pman:latest

Start pman
==========

.. code-block:: bash

    docker swarm init --advertise-addr=127.0.0.1
    docker run --rm --name pman                       \
        -p 127.0.0.1:5010:5010                        \
        -v /var/run/docker.sock:/var/run/docker.sock  \
        -v $PWD/FS/remote:/home/localuser/storeBase           \
        -e STOREBASE=$PWD/FS/remote                   \
        fnndsc/pman:latest

Example Job
===========

Simulate incoming data

.. codde-block:: bash

    docker exec pman bash -c 'mkdir /home/localuser/somedata && touch /home/localuser/somedata/something'


Using `HTTPie <https://httpie.org/>` to run a container

.. code-block:: bash

    http :5010 payload:='{
        "action": "run",
        "meta": {
            "cmd": "ls /share",
            "threaded": true,
            "auid": "someone",
            "jid": "a-job-id-2",
            "number_of_workers": "1",
            "cpu_limit": "1000",
            "memory_limit": "200",
            "gpu_limit": "0",
            "container": {
                "target": {
                    "image": "fnndsc/pl-simpledsapp:version-1.0.8",
                    "cmdParse": false
                },
                "manager": {
                    "image": "fnndsc/swarm",
                    "app": "swarm.py",
                    "env": {
                        "meta-store": "key",
                        "serviceType": "docker",
                        "shareDir": "/home/localuser/somedata/",
                        "serviceName": "testService"
                    }
                }
            }
        }
    }'

Get the result

.. code-block: bash

    http :5010/api/v1/cmd payload:='{
        "action": "status",
            "meta": {
                    "key":          "jid",
                    "value":        "a-job-id-2"
            }
        }'

``pman`` usage
===============

For ``pman`` detailed information, see the `pman wiki page <https://github.com/FNNDSC/pman/wiki/pman-overview>`_.

.. code-block:: html

    ARGS

        [--ip <IP>]

        The IP interface on which to listen.

        [--port <port>]
        The port on which to listen. Defaults to '5010'.

        [--enableTokenAuth]
        Enables token based authorization and can be configured to look
        for a .ini file or an openshift secret.

        [--tokenPath <tokenPath>]
        Specify the absolute path to the token in the file system.
        By default, this looks for the pfiohConfig.ini file in the current
        working directory.

        [-x|--desc]
        Provide an overview help page.

        [-y|--synopsis]
        Provide a synopsis help summary.

        [--version]
        Print internal version number and exit.

        [-v|--verbosity <level>]
        Set the verbosity level. "0" typically means no/minimal output.
        Allows for more fine tuned output control as opposed to '--quiet'
        that effectively silences everything.
