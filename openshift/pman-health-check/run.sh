#!/bin/bash


pfurl --verb POST --raw --http $hosturl/api/v1/cmd:5010/api/v1/cmd --jsonwrapper 'payload' --msg \
 '{  "action": "hello",
         "meta": {
                 "askAbout":     "sysinfo",
                 "echoBack":     "Hi there!"
         }
 }' --quiet --jsonpprintindent 4
