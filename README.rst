#################
pman - v2.0.0.8
#################

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

This repository proves ``pman`` -- a process manager. 

pman
====

Most simply, ``pman`` manages processes, i.e. programs or applications that are run by an underlying system. Typically, these processes are command line applications (i.e. have no GUI) and usually do not interact really with a user at all. The primary purpose of ``pman`` is to provide other software agents the ability to execute processes via ``http``.

Originally, ``pman`` was designed to track simple processes executed on the local system. In addition, ``pman`` keeps a record of the current and historical state of processes that it has executed and is thus able to respond to queries about the processes. Some of the queries that ``pman`` can address are

- *state*: Is job <XYZ> still running?
- *result*: What is the stdout (or stderr) from job <XYZ>?
- *control*: Kill job <XYZ>

``pman`` also maintains a persistent human-readable/friendly database-in-the-filesystem of jobs and states of jobs.

Current versions of ``pman`` however can use container-based backends (swarm and openshift) to execute processes. In those cases, the internal database of tracking jobs becomes superfluous. Future versions of ``pman`` might depreciate the local/internal DB tracking.


************
Installation
************

Installation is relatively straightforward, and we recommend using either python virtual environments or docker.

Python Virtual Environment
==========================

On Ubuntu, install the Python virtual environment creator

.. code-block:: bash

  sudo apt install virtualenv virtualenvwrapper

Then, create a directory for your virtual environments e.g.:

.. code-block:: bash

  mkdir ~/python-envs

You might want to add to your .bashrc file these two lines:

.. code-block:: bash

    export WORKON_HOME=~/python-envs
    source /usr/local/bin/virtualenvwrapper.sh

(Note depending on distro, the ``virtualenvwrapper.sh`` path might be

.. code-block:: bash
    
    /usr/share/virtualenvwrapper/virtualenvwrapper.sh

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
  

Using the ``fnndsc/pman`` dock
==============================

The easiest option however, is to just use the ``fnndsc/pman`` dock.

.. code-block:: bash

    docker pull fnndsc/pman
    
and then run

.. code-block:: bash

    docker run  --name pman         \
                -v /home:/Users     \
                --rm -ti            \
                fnndsc/pman         \
                --rawmode 1 --http  \
                --port 5010         \
                --listeners 12

*****
Usage
*****

``pman`` usage
===============

For ``pman`` detailed information, see the `pman wiki page <https://github.com/FNNDSC/pman/wiki/pman-overview>`_.

.. code-block:: html

    ARGS

        [--ip <IP>]                            

        The IP interface on which to listen.

        [--port <port>]
        The port on which to listen. Defaults to '5010'.

        [--protocol <protcol>]
        The protocol to interpret. Defaults to 'tcp'.

        [--rawmode]
        Internal zmq socket server mode. A value of '1' is usually used
        here.

        [--listeners <numberOfListenerThreads>]
        The number of internal threads to which requests are dispatched.

        [--http]
        Send return strings as HTTP formatted replies with content-type html.

        [--debugToFile]
        If specified, send debugging results to file.

        [--debugToFile <file>]
        In conjunction with --debugToFile, file which will receive debugging info.

        [--listenerSleep <time>]
        A small delay in the listener loop to prevent busy-wait.
        Default is 0.1 seconds.

        [--DBsavePeriod <time>]
        The periodicity in seconds for the internal DB save.

        [--enableTokenAuth]
        Enables token based authorization and can be configured to look for a .ini
        file or an openshift secret.

        [--tokenPath <tokenPath>]
        Specify the absolute path to the token in the file system.
        By default, this looks for the pfiohConfig.ini file in the current working directory.

        [-x|--desc]                                     
        Provide an overview help page.

        [-y|--synopsis]
        Provide a synopsis help summary.

        [--version]
        Print internal version number and exit.

        [-v|--verbosity <level>]
        Set the verbosity level. "0" typically means no/minimal output. Allows for
        more fine tuned output control as opposed to '--quiet' that effectively
        silences everything.

        --container-env <env>
        The container env within which to run.

********    
EXAMPLES
********

Start ``pman`` with 12 listeners:

.. code-block:: bash

        pman                                                        \\
                --ip 127.0.0.1                                      \\
                --port 5010                                         \\
                --rawmode 1                                         \\
                --http                                              \\
                --listeners 12                                      \\
                --verbosity 1
