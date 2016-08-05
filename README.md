# pman

## Overview

'pman.py' is a process management system that launches and tracks the status of jobs. In the most general sense, jobs are simply applications run on an underlying system shell.

## TL;DR

In the simplest case, a job can be submitted to 'pman' using a REST type interface

```
http POST http://10.17.24.163:5010/api/v1/cmd/ Content-Type:application/json Accept:application/json payload:='{"exec": {"cmd": "cal 7 1970"}, "action":"run","meta":{"jid": "123-456-1", "auid": "rudolphpienaar"}}'
```

'pman.py' will then spawn the process and provide information on the status of the job. Note the <tt>payload</tt> JSON dictionary that provides some additional behaviour options (see later).

Jobs launched by 'pman.py' can be queried with

```
http GET http://10.17.24.163:5010/api/v1/_01/endInfo Content-Type:application/json Accept:application/json
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

