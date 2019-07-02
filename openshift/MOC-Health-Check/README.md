# MOC Health Reporter - v1.0

********
***Overview***
********

This repository provides a real-world application for pfurl project. It sends a generic command from pfurl to send local files to Pfioh, run a sample job on Pman, and fetch the files back from Pfioh. Overall, it tests all of the core elements of Chris Platform, informing personnel if an issue pertains for a long peridod of time. 


- ``MOC Status Reporter``: a program to test the functionality of MOC 

MOC Health Reporter
=====

``MOC Health Reporter`` is an extension of the ``pf`` family of utilities, since it successfully utilizes pfurl as a testing service for ChRIS Research Integration System.

In layman's terms, ``MOC Health Reporter`` is a status fetcher used to send http-based messages to remote services such as ``pman`` and ``pfioh``, in order to test their efficiency and response time. In addition to recieving status codes, the program also provides a standard of communication with specific recipients, conveying the status of MOC to raise awareness of prolonged issues in the service. 

It also posseses the capability to run in a containerized atmosphere, requiring no external communication with other modules. 

************
Installation
************

Installation is easy on Linux environments with python and continuous integration applications

Python Environments
==========================

On any Linux OS, clone this repository and change arguments of config.cfg

      sudo vim config.cfg

Edit the recipients.txt as per your requirements

      sudo vim recipients.txt

Install requirements of Python

     bash setup.sh
     
Run the program 
     
     python3 automate.py


Travis CI
==========================

First, fork this repository to your github, clone it to your computer, and change arguments of config.cfg

      sudo vim config.cfg

Edit the recipients.txt as per your requirements

      sudo vim recipients.txt

Commit your changes and push them to your github

     git add .; git commit -m "message"; git push
     
Run the program on Travis Web Application 
     



