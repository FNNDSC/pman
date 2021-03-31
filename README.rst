###########
pman v3.0.0
###########

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

This repository implements ``pman`` -- a process manager that provides a unified API over HTTP for running jobs on

* docker swarm
* Openshift

***********************
Development and testing
***********************

Preconditions
=============

Install latest Docker and Docker Compose
----------------------------------------

Currently tested platforms:

* ``Ubuntu 18.04+ and MAC OS X 10.14+ and Fedora 31+`` ([Additional instructions for Fedora](https://github.com/mairin/ChRIS_store/wiki/Getting-the-ChRIS-Store-to-work-on-Fedora))
* ``Docker 18.06.0+``
* ``Docker Compose 1.27.0+``

Note: On a Linux machine make sure to add your computer user to the ``docker`` group.
Consult this page https://docs.docker.com/engine/install/linux-postinstall/

Start pman's Flask development server
=====================================

.. code-block:: bash

    git clone https://github.com/FNNDSC/pman.git
    cd pman
    ./make.sh

You can later remove all the backend containers with:

.. code-block:: bash

    $> cd pman
    $> ./unmake.sh


Example Job
===========

Simulate incoming data

.. code-block:: bash

    pman_dev=$(docker ps -f ancestor=fnndsc/pman:dev -f name=pman_service -q)  
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
