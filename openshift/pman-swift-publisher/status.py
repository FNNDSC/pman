import json
import sys

jdata = sys.stdin.read()
data = json.loads(jdata)

# Check if the image processing container is still running
for status in data['status']['containerStatuses']:
    if status['name'] != 'publish':
      if status['state']['terminated']:
        exit(0)

exit(1)
