#!/usr/bin/env python3

import sys, os
sys.path.append(os.path.abspath('../'))
import subprocess, os
from subprocess import Popen, PIPE
import shlex

"""
Creates "test" directories of varying sizes on which the pman and pfioh tests will be performed
"""

def getsize(thisDir):
    total = 0
    for x in os.listdir(thisDir):
        dirpath = '%s/%s' % (thisDir, x)
        fsize = os.path.getsize(dirpath)
        total += fsize

    total /= (1024 * 1024)
    return total

def check():

    if not (os.path.exists('/tmp/share')):
        subprocess.call('mkdir /tmp/share', shell=True)

    if not (os.path.exists('/tmp/small') and os.path.exists('/tmp/medium') and os.path.exists('/tmp/large') and os.path.exists('/tmp/xlarge')):
        subprocess.call('mkdir /tmp/xlarge', shell=True)
        subprocess.call('mkdir /tmp/large', shell=True)
        subprocess.call('mkdir /tmp/medium', shell=True)
        subprocess.call('mkdir /tmp/small', shell=True)

    if not ((getsize('/tmp/small') == 1) and (getsize('/tmp/medium') == 25) and (getsize('/tmp/large') == 100)):
            create()

def create():
    """                                                                                                                                                   
    Create directories (small, medium, large)                                                                                                            
    """

    count = 0

    # Fill SMALL directory: should sum to 1MB
    make_file(count, '1', 'small')
    count += 1

    # Fill MEDIUM directory: should sum to 25MB
    for x in range(25):
        make_file(count, '1', 'medium')
        count += 1

    # Fill LARGE directory: should sum to 100MB
    for n in range(4):
        make_file(count, '25', 'large')
        count += 1

    # Fill XLARGE directory: should sum to 1GB
    for n in range(10):
        make_file(count, '100', 'xlarge')
        count += 1

    print ("done creating files\n")

def clean():

    if (os.path.exists('/tmp/share')):
        for x in os.listdir('/tmp/share/'):
            cmd = 'sudo rm -rf /tmp/share/%s' % x
            subprocess.call(shlex.split(cmd), shell=False)

    
def make_file(fid, size, place):
    """                                                                                                                                     
    Create a file of size 'size' in 'place'                                                                 
    """

    print ("creating file of size " + size + " in /tmp/" + place)
    process = Popen(['bash', 'create_file.sh', str(fid), size,  place], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()


clean()
check()