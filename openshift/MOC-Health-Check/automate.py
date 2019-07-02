import os, subprocess, time
from health_checker import rate, rate2, rate3, rate4, THRESHOLD

while True:
    subprocess.call("health-checker.py", shell=True)

    success_pfioh_push = int(rate)
    success_pman_run = int(rate2)
    success_pman_status = int(rate3) 
    success_pfioh_pull = int(rate4) 
    threshold = int(THRESHOLD) 
    
    state = True
    msg = ""
 
 
    if threshold > success_pfioh_push:
        msg = ", Pfioh Push"
        state = False
    if threshold > success_pman_run:
        msg += ", Pman Run"
        state = False
    if threshold > success_pman_status:
        msg += ", Pman Status"
        state = False
    if threshold > success_pfioh_pull:
        msg += ", Pfioh Pull"
        state = False
    
    msg = msg[2:]

    if state == False:
        subprocess.call("python3 mail.py -i " + '"' + msg + '"' ,shell=True)
        break