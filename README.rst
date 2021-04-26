########################
pman v3.0.0 |ChRIS logo|
########################

.. |ChRIS logo| image:: https://github.com/FNNDSC/ChRIS_ultron_backEnd/blob/master/docs/assets/logo_chris.png

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
    :depth: 2

********
Overview
********

This repository implements ``pman`` -- a process manager that provides a unified API over HTTP for running jobs on

* Docker Swarm
* Kubernetes
* Openshift

***********************
Development and testing
***********************

Preconditions
=============

Install latest docker
---------------------

Currently tested platforms:

* ``Ubuntu 18.04+ and MAC OS X 10.14+ and Fedora 31+`` `Additional instructions for Fedora <https://github.com/mairin/ChRIS_store/wiki/Getting-the-ChRIS-Store-to-work-on-Fedora>`_
* ``Docker 18.06.0+``

Note: On a Linux machine make sure to add your computer user to the ``docker`` group.
Consult this page https://docs.docker.com/engine/install/linux-postinstall/


Docker Swarm-based development environment
==========================================

Start a local Docker Swarm cluster if not already started
---------------------------------------------------------

.. code-block:: bash

    $> docker swarm init --advertise-addr 127.0.0.1

Start pman's Flask development server
-------------------------------------

.. code-block:: bash

    $> git clone https://github.com/FNNDSC/pman.git
    $> cd pman
    $> ./make.sh

Remove pman's Flask development server
--------------------------------------

.. code-block:: bash

    $> cd pman
    $> ./unmake.sh

Remove the local Docker Swarm cluster if desired
------------------------------------------------

.. code-block:: bash

    $> docker swarm leave --force


Kubernetes-based development environment
========================================

Install single-node Kubernetes cluster
--------------------------------------

On MAC OS Docker Desktop includes a standalone Kubernetes server and client. Consult this page https://docs.docker.com/desktop/kubernetes/

On Linux there is a simple MicroK8s installation. Consult this page https://microk8s.io
Then create the required alias:

.. code-block:: bash

    $> snap alias microk8s.kubectl kubectl
    $> microk8s.kubectl config view --raw > $HOME/.kube/config


Start pman's Flask development server
-------------------------------------

.. code-block:: bash

    $> git clone https://github.com/FNNDSC/pman.git
    $> cd pman
    $> ./make.sh -O kubernetes

Remove pman's Flask development server
--------------------------------------

.. code-block:: bash

    $> cd pman
    $> ./unmake.sh -O kubernetes


Example Job
===========

Simulate incoming data
----------------------

Docker Swarm:

.. code-block:: bash

    $> pman_dev=$(docker ps -f name=pman_dev_stack_pman_service.1 -q)
    $> docker exec $pman_dev mkdir -p /home/localuser/storeBase/key-chris-jid-1/incoming
    $> docker exec $pman_dev mkdir -p /home/localuser/storeBase/key-chris-jid-1/outgoing
    $> docker exec $pman_dev touch /home/localuser/storeBase/key-chris-jid-1/incoming/test.txt

Kubernetes:

.. code-block:: bash

    $> pman_dev=$(kubectl get pods --selector="app=pman,env=development" --output=jsonpath='{.items[*].metadata.name}')
    $> kubectl exec $pman_dev -- mkdir -p /home/localuser/storeBase/key-chris-jid-1/incoming
    $> kubectl exec $pman_dev -- mkdir -p /home/localuser/storeBase/key-chris-jid-1/outgoing
    $> kubectl exec $pman_dev -- touch /home/localuser/storeBase/key-chris-jid-1/incoming/test.txt


Using `HTTPie <https://httpie.org/>` to run a container

.. code-block:: bash

    $> http POST http://localhost:30010/api/v1/ cmd_args='--saveinputmeta --saveoutputmeta --dir cube/uploads' cmd_path_flags='--dir' auid=cube number_of_workers=1 cpu_limit=1000 memory_limit=200 gpu_limit=0 image=fnndsc/pl-dircopy selfexec=dircopy selfpath=/usr/local/bin execshell=/usr/local/bin/python type=fs jid=chris-jid-1

Get the result

.. code-block:: bash

    $> http http://localhost:30010/api/v1/chris-jid-1/
    

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
