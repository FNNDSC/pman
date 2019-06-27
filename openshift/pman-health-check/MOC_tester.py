#!/usr/bin/env python3

from email.mime.text import MIMEText
import re                                                                                                                                                 
from subprocess import PIPE
from time import sleep
import smtplib
import subprocess, re, os, tempfile, sys, optparse, argparse
import urllib.request
import os

envVar = subprocess.Popen(["/bin/sh", "source setup.sh"],shell=True)
username_email = os.environ['Email']
password_email = os.environ['Password']
body_email = os.environ['Body']
subject_email = os.environ['Subject']
waitTime = os.environ['Wait']
error_count = os.environ['ErrorCount']
iterations = os.environ['Iterations']

def command():                                                                                    
	code = subprocess.Popen("sh run.sh", shell=True,stdout=subprocess.PIPE)                                                                      
	output = code.stdout.read()                                                     
	output = str(output, "utf-8")
	print(output)
	global valid
	if "true" in output:
		valid = True
	else:
		valid = False 




def email():
	username = username_email # be sure to allow less secure apps to connect with this gmail account
	password = password_email # https://myaccount.google.com/u/1/lesssecureapps?pli=1&pageId=none
	recip = []
	body = "" + body_email 
	with open('recip.txt') as file:
		recip = file.read().splitlines()
	msg = MIMEText(body)
	msg['Subject'] = subject_email

	msg['From'] = username
	msg['To'] = ', '.join(recip)
	print(recip) 
	print(msg)
	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.ehlo()
	server.starttls()
	server.login(username, password)
	server.sendmail(username, recip, msg.as_string())
	server.quit()

global run_time
global count
run_time = 0
count = 0
while True:
	# count refers to the count of HTTP status code errors
	# run_time refers to no. of times the pfurl command ran 
	command()
	if(run_time>=int(iterations)):
		count = 0
		run_time = 0
	if valid is False:
		count = count + 1
		if(count > int(error_count)):
			email()
	run_time = run_time + 1
	print(count)
	print(run_time)
	sleep(int(waitTime))


