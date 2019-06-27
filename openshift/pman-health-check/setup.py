import subprocess

subprocess.call("pip3 install pfurl", shell=True)

try:
	subprocess.call("apt-get install -y libssl-dev libcurl4-openssl-dev bsdmainutils vim net-tools inetutils-ping")
except Exception:
	pass

