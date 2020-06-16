import sys
# Make sure we are running python3.5+
if 10 * sys.version_info[0]  + sys.version_info[1] < 35:
    sys.exit("Sorry, only Python 3.5+ is supported.")

from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(
      name             =   'pman',
      version          =   '2.2.0.0',
      description      =   '(Python) Process Manager',
      long_description =   readme(),
      author           =   'Rudolph Pienaar',
      author_email     =   'rudolph.pienaar@gmail.com',
      url              =   'https://github.com/FNNDSC/pman',
      packages         =   ['pman'],
      install_requires =   ['pycurl', 'pyzmq', 'webob', 'pudb', 'psutil', 'docker', 'openshift', 'pfmisc', 'ipaddress', 'fasteners', 'kubernetes', 'python-keystoneclient'],
      test_suite       =   'nose.collector',
      tests_require    =   ['nose'],
      scripts          =   ['bin/pman', 'bin/pman_do'],
      license          =   'MIT',
      zip_safe         =   False
     )
