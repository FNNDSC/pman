##################
pman - v1.6.9.dev0
##################

.. image:: https://badge.fury.io/py/pman.svg
    :target: https://badge.fury.io/py/pman

.. image:: https://travis-ci.org/FNNDSC/pman.svg?branch=master
    :target: https://travis-ci.org/FNNDSC/pman

.. image:: https://img.shields.io/badge/python-3.5%2B-blue.svg
    :target: https://badge.fury.io/py/pman

.. contents:: Table of Contents

********
Overview
********

This repository proves ``pman`` -- a process manager. This is a bleeding edge development branch.

pman
====

Most simply, ``pman`` manages processes, i.e. programs or applications that are run by an underlying system. Typically, these processes are command line applications (i.e. have no GUI) and usually do not interact really with a user at all. The primary purpose of ``pman`` is to provide other software agents the ability to execute processes via ``http``. In addition, ``pman`` keeps a record of the current and historical state of processes that it has executed and is thus able to respond to queries about the processes. Some of the queries that ``pman`` can address are

- *state*: Is job <XYZ> still running?
- *result*: What is the stdout (or stderr) from job <XYZ>?
- *control*: Kill job <XYZ>

``pman`` also maintains a persistent human-readable/friendly database-in-the-filesystem of jobs and states of jobs.


************
Installation
************

Installation is relatively straightforward, and we recommend using either python virtual environments or docker.

Python Virtual Environment
==========================

On Ubuntu, install the Python virtual environment creator

.. code-block:: bash

  sudo apt install virtualenv

Then, create a directory for your virtual environments e.g.:

.. code-block:: bash

  mkdir ~/python-envs

You might want to add to your .bashrc file these two lines:

.. code-block:: bash

    export WORKON_HOME=~/python-envs
    source /usr/local/bin/virtualenvwrapper.sh

Then you can source your .bashrc and create a new Python3 virtual environment:

.. code-block:: bash

    source .bashrc
    mkvirtualenv --python=python3 python_env

To activate or "enter" the virtual env:

.. code-block:: bash

    workon python_env

To deactivate virtual env:

.. code-block:: bash

    deactivate

Using the ``fnndsc/ubuntu-python3`` dock
========================================

We provide a slim docker image with python3 based off Ubuntu. If you want to play inside this dock and install ``pman`` manually, do

.. code-block:: bash

    docker pull fnndsc/ubuntu-python3

This docker has an entry point ``python3``. To enter the dock at a different entry and install your own stuff:

.. code-block:: bash

   docker run -ti --entrypoint /bin/bash fnndsc/ubuntu-python3
   
Now, install ``pman`` and friends using ``pip``

.. code-block:: bash

   apt update && \
   apt install -y libssl-dev libcurl4-openssl-dev librtmp-dev && \
   pip install pman
   
**If you do the above, remember to** ``commit`` **your changes to the docker image otherwise they'll be lost when you remove the dock instance!**

.. code-block:: bash

  docker commit <container-ID> local/ubuntu-python3-pman
  
 where ``<container-ID>`` is the ID of the above container.
  

Using the ``fnndsc/pman`` dock
==============================

The easiest option however, is to just use the ``fnndsc/pman`` dock.

.. code-block:: bash

    docker pull fnndsc/pman
    
and then run

.. code-block:: bash

    docker run --name pman -v /home:/Users --rm -ti fnndsc/pman --rawmode 1 --http --port 5010 --listeners 12

*****
Usage
*****

``pman`` usage
===============

For ``pman`` detailed information, see the `pman wiki page <https://github.com/FNNDSC/pman/wiki/pman-overview>`_.

