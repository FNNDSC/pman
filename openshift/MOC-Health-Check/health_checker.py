import os, sys
import configparser
from subprocess import Popen, PIPE
import test_setup
import subprocess
import time
"""
Performs scalability and performance tests by making increasingly more concurrent requests to pman and capturing resource utilization
"""


s_rate = 0                               # Success rate of pfioh_push

s_rate2 = 0                               # Success rate of pman_run

s_rate3 = 0                               # Success rate of pman_status

s_rate4 = 0                               # Success rate of pfioh_pull

config = configparser.ConfigParser()
config.read('config.cfg')

RANGE = int(config.get('ConfigInfo', 'RANGE'))
SIZE = config.get('ConfigInfo', 'SIZE')
TIMEOUT = config.get('ConfigInfo', 'TIMEOUT')
THRESHOLD = config.get('ConfigInfo', 'THRESHOLD')
PATH = os.getcwd()
WAIT = config.get('ConfigInfo', 'WAIT')
test_setup.check()

def job_delete():
    cmd = 'bash %s/run_pman_delete %s ' % (PATH, JID)
    command = subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE)
    output = command.stdout.read()                                                     
    output = str(output, "utf-8")
    print(output)


for x in range(1, RANGE + 1):
    global JID
    JID = "healthcheckfinal" #+ str(x)

    print("Iteration " + str(x))
    print("_________________")

    cmd = 'bash %s/run_pfioh_push %s %s' % (PATH, JID, SIZE)
    command = subprocess.Popen("timeout " + TIMEOUT + " " + cmd,shell=True, stdout=subprocess.PIPE)
    print(cmd)  	
    output = command.stdout.read()                                                     
    output = str(output, "utf-8")
    if "true" in output:
        s_rate = s_rate + 1
        cmd = 'bash %s/run_pman %s ' % (PATH, str(JID))
        print(cmd)
        command = subprocess.Popen("timeout " + TIMEOUT + " " + cmd,shell=True, stdout=subprocess.PIPE)
        output = command.stdout.read()                                                     
        output = str(output, "utf-8")
        if "true" in output:
            s_rate2 = s_rate2 + 1
            num = 0
            while num<20:
                cmd = 'bash %s/run_pman_status %s' % (PATH, JID)
                print(cmd)
                command = subprocess.Popen("timeout " + TIMEOUT + " " +  cmd,shell=True, stdout=subprocess.PIPE)
                output = command.stdout.read()                                                     
                output = str(output, "utf-8")
                print(output)
                if "finished" in output:
                    break
                else:
                    time.sleep(int(WAIT))
                    num = num + 1
            if "finished" in output:
                s_rate3 = s_rate3 + 1   
                cmd = 'bash %s/run_pfioh_pull %s %s' % (PATH, JID, SIZE)
                command = subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE)
                print(cmd)  	
                output = command.stdout.read()                                                     
                output = str(output, "utf-8")
                print(output)
                if "true" in output:
                    s_rate4 = s_rate4 + 1
                    job_delete()
                else:
                    print("Error in Pfioh pull")
        
            else: 
                print("Error in obtaining a complete status of Pman's job")
                job_delete()
        else:
            print("Error in running job in Pman")
    else:
        print("Error in Pfioh push")



rate  = str(int((s_rate/RANGE)*100))
rate2 = str(int((s_rate2/RANGE)*100))
rate3 = str(int((s_rate3/RANGE)*100))
rate4 = str(int((s_rate4/RANGE)*100))
