# MOC Status Reporter - v1.0

********
***Overview***
********

This repository provides a real-world applocation for pfurl project. It sends a generic command from pfurl, and recieves a unique output: a “true” status as its output when server performs exceptionally and an http error code if it is unable to properly communicate with the MOC server. Thus, the program is designed to send an email to a list of recipients if pfurl displays a http status code several times in a given period of time. 


- ``MOC Status Reporter``: a program to test the functionality of MOC (similar to ``curl's -I command``);

MOC Status Reporter
=====

``MOC Status Reporter`` is an extension of the ``pf`` family of utilities, since it successfully utilizes pfurl as a testing service for ChRIS Research Integration System.

In layman's terms, ``MSR`` is a status fetcher used to send http-based messages to remote services such as ``pman`` and ``pfioh``, in order to test their efficiency. In addition to recieving status codes, ``MSR`` also provides a standard of communication with specific recipients, conveying the status of MOC to raise awareness of prolonged issues in the service. 

It also possesed the capability to run in a containerized atmosphere, requiring no external communication with other modules. 

************
Installation
************

Installation is easy on Linux environments and python applications, perfoming exceptional in python applications or Docker.

Docker Client
==========================

On Ubuntu, clone this repository and change env arguments of Dockerfile

      sudo vim Dockerfile

Edit the recipients.txt as per your requirements

      sudo vim recip.txt

Go to previous directory & build the docker image

     cd ..;docker build MOC_Status_Reporter
     
Run the Docker Image to create a container 
     
     docker run <container_name>

Python Environments
==========================

On any Linux OS, clone this repository and change env arguments of setup.sh

      sudo vim setup.sh

Edit the recipients.txt as per your requirements

      sudo vim recip.txt

Install requirements of Python

     python3 setup.py
     
Run the program 
     
     python3 MOC_tester.py





