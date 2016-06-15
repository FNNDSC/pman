# pman

## Overview

'pman' is a process management system written in python. Its main purpose is to act as a service that launches and tracks the status of jobs.

## TL;DR

In the simplest case, a job can be submitted to 'pman' using a REST type interface

```
POST pman.com/api/v1/cmd '{"cmd": "someExecutable", "args":["arg1", "arg2", arg3", "arg4"]}'
```

'pman' will then spawn the process and keep polling the system process table for the job and track the stdout/stderr and exit code.

Jobs launched by 'pman' can be queried with

```
GET pman.com/api/v1/
```

for a list of all running jobs, while specific detail about a given job can be queried with

```
GET pman.com/api/v1/1/pid
GET pman.com/api/v1/1/status
GET pman.com/api/v1/1/cmd
... 

```

for the pid and status of job "1", for example

## Dependencies

On Ubuntu, 'pman' relies on <tt>webob</tt> and <tt>zmq</tt>

```
sudo apt install python-zmq python-webob
```

Also, a useful CLI REST tool is the python <tt>http</tt>

```
sudo apt install httpie
```

