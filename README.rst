####################################
Pman - v0.10.3
####################################

.. image:: https://badge.fury.io/py/pman.svg
    :target: https://badge.fury.io/py/pman

.. image:: https://travis-ci.org/FNNDSC/pman.svg?branch=master
    :target: https://travis-ci.org/FNNDSC/pman

.. image:: https://img.shields.io/badge/python-3.5%2B-blue.svg
    :target: https://badge.fury.io/py/pman

***************
1. Overview
***************

'pman' is a process management system that launches and tracks the status of jobs. In the most general sense, jobs are simply applications run on an underlying system shell.

***************
2. Installation
***************

.. code-block:: bash

   apt install python-zmq python-webob
   pip install pman
   # optional
   pip install httpie

***************
3. Usage
***************

Scripts
===============

.. code-block:: bash

   # start 'pman', listening on port 5010 of the current host
   pman --raw 1 --http  --port 5010 --listeners 12

Modules
===============

.. code-block:: python

   # in yourscript.py
   import pman

   pman.pman(
     debugFile = '/tmp/debug.file'
     )


***************
4. More
***************

.. code-block:: bash

   pman.py --raw 1 --http  --port 5010 --listeners 12

Now, assuming the IP of the host as below, a job can be submitted to 'pman' using a REST type interface

.. code-block:: bash

   http POST http://10.17.24.163:5010/api/v1/cmd/ \
   Content-Type:application/json Accept:application/json \
   payload:='
     {
     "exec": {"cmd": "cal 7 1970"}, 
     "action":"run",
     "meta": {
         "jid": "123-456-1", 
         "auid": "rudolphpienaar"
       }
     }'

'pman' will then spawn the process and provide information on the status of the job. Note the <tt>payload</tt> JSON dictionary that provides some additional behaviour options (see later).

Jobs launched by 'pman.py' can be queried with

.. code-block:: bash

   http GET http://10.17.24.163:5010/api/v1/_01/endInfo \
     Content-Type:application/json Accept:application/json

for the pid and status of job "1", for example
