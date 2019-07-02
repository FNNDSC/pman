import configparser
import smtplib
from email.mime.text import MIMEText
import argparse
config = configparser.ConfigParser()
config.read('config.cfg')

username_email = config.get('ConfigInfo', 'EMAIL')
password_email = config.get('ConfigInfo','PASSWORD')
body_email = config.get('ConfigInfo','BODY')
subject_email = config.get('ConfigInfo','SUBJECT')

def get_arguments():
	parser = argparse.ArgumentParser(description='Email Sender Options')
	parser.add_argument("-i", "--issue", dest="issue", help="Issue in Chris Framework", required=True)
	return parser.parse_args()


arguments = get_arguments()
issue = arguments.issue

def email():
	username = username_email # be sure to allow less secure apps to connect with this gmail account
	password = password_email # https://myaccount.google.com/u/1/lesssecureapps?pli=1&pageId=none
	recip = []
	body = "" + body_email 
	with open('recipients.txt') as file:
		recip = file.read().splitlines()
	msg = MIMEText(body + " " + issue)
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
email()