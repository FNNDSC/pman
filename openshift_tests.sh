#!/bin/bash
cd ..
ls -la

pip install pfurl

echo '______________________________________________________________'

export HOST_IP=$(ip route | grep -v docker | awk '{if(NF==11) print $9}')
export HOST_PORT=8000
export DICOMDIR=$(pwd)/SAG-anon

echo $HOST_PORT
docker ps


echo $HOST_IP
echo $pman_route
echo $pfioh_route

# Say hello to pmana and pfioh on 

pfurl --verb POST --raw \
      --http ${HOST_IP}:5005/api/v1/cmd \
      --httpResponseBodyParse \
      --jsonwrapper 'payload' \
      --msg \
'{  "action": "internalctl",
    "meta": {
                "var":     "/service/moc",
                "set":     {
                    "compute": {
                        "addr": ${pman_route},
                        "baseURLpath": "api/v1/cmd/",
                        "status": "undefined",
                        "authToken": "{Bu7H)FyWp{,e<"
                    },
                    "data": {
                        "addr": ${pfioh_route},
                        "baseURLpath": "api/v1/cmd/",
                        "status": "undefined",
                        "authToken": "{Bu7H)FyWp{,e<"
                    }
                }
            }
}'

# Test with a hello

pfurl --verb POST --raw --http ${HOST_IP}:5005/api/v1/cmd   \
        --httpResponseBodyParse --jsonwrapper 'payload' --msg \
'{  "action": "hello",
    "meta": {
                "askAbout":     "sysinfo",
                "echoBack":      "Hi there!",
                "service":       "moc"
            }
}'

# # PUSH data into open storage
# ./swiftCtl.sh -A push -E dcm -D $DICOMDIR -P chris/uploads/DICOM/dataset1

# # Verify
# ./swiftCtl.sh

# # Create the equivalent of an FS feed
# pfurl \
#                     --verb POST --raw --http ${HOST_IP}:5005/api/v1/cmd \
#                     --httpResponseBodyParse                             \
#                     --jsonwrapper 'payload' --msg '
#             {
#     "action": "coordinate",
#     "meta-compute": {
#         "auid": "chris",
#         "cmd": "python3 /usr/src/dircopy/dircopy.py --dir /share/incoming /share/outgoing",
#         "container": {
#             "manager": {
#                 "app": "swarm.py",
#                 "env": {
#                     "meta-store": "key",
#                     "serviceName": "1",
#                     "serviceType": "docker",
#                     "shareDir": "%shareDir"
#                 },
#                 "image": "fnndsc/swarm"
#             },
#             "target": {
#                 "cmdParse": false,
#                 "execshell": "python3",
#                 "image": "fnndsc/pl-dircopy",
#                 "selfexec": "dircopy.py",
#                 "selfpath": "/usr/src/dircopy"
#             }
#         },
#         "cpu_limit": "1000m",
#         "gpu_limit": 0,
#         "jid": "trytry22",
#         "memory_limit": "200Mi",
#         "number_of_workers": "2",
#         "service": "host",
#         "threaded": true
#     },
#     "meta-data": {
#         "localSource": {
#             "path": "chris/uploads/DICOM/dataset1",
#             "storageType": "swift"
#         },
#         "localTarget": {
# 		"path": "chris/feed_1/dircopy_1/data",
# 		"createDir":    true
#         },
#         "local": {
#             "path":  "/tmp/share/trytry22",
#             "createDir":    true
#         },
#         "remote": {
#             "key": "trytry22"
#         },
#         "service": "host",
#         "transport": {
#             "compress": {
#                 "archive": "zip",
#                 "cleanup": true,
#                 "unpack": true
#             },
#             "mechanism": "compress"
#         }
#     },
#     "meta-store": {
#         "key": "jid",
#         "meta": "meta-compute"
#     },
#     "threadAction": true
# } ' --quiet --jsonpprintindent 4