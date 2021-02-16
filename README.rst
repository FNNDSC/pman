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

This repository provides ``pman`` -- a process manager, that provides a unified API over HTTP for running jobs on

* docker swarm
* Openshift

For more info see
https://github.com/FNNDSC/pman/wiki/pman-overview

***********
Basic Usage
***********

The most common use case for ``pman`` is for running jobs against *docker swarm*.


Start pman
==========

.. code-block:: bash

    git clone https://github.com/FNNDSC/pman.git
    cd pman
    git checkout flask
    docker build -t local/pman:dev .
    
In ``docker-compose_dev.yml`` change ``PMANREPO`` to ``local``

.. code-block:: bash

    ./make.sh
    

Example Job
===========

Simulate incoming data

.. code-block:: bash

    pman_dev=$(docker ps -f ancestor=local/pman:dev -f name=pman_service -q)  
    docker exec -it $pman_dev mkdir -p /home/localuser/storeBase/key-chris-jid-1/incoming
    docker exec -it $pman_dev mkdir -p /home/localuser/storeBase/key-chris-jid-1/outgoing
    docker exec -it $pman_dev touch /home/localuser/storeBase/key-chris-jid-1/incoming/test.txt


Using `HTTPie <https://httpie.org/>` to run a container

.. code-block:: bash

    http POST http://localhost:5010/api/v1/ cmd_args='--saveinputmeta --saveoutputmeta --dir cube/uploads' cmd_path_flags='--dir' auid=cube number_of_workers=1 cpu_limit=1000 memory_limit=200 gpu_limit=0 image=fnndsc/pl-dircopy selfexec=dircopy selfpath=/usr/local/bin execshell=/usr/local/bin/python type=fs jid=chris-jid-1

Get the result

.. code-block:: bash

    http http://localhost:5010/api/v1/chris-jid-1/
    

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
