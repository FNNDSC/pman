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
      version          =   '1.6.12.2',
      description      =   '(Python) Process Manager',
      long_description =   readme(),
      author           =   'Rudolph Pienaar',
      author_email     =   'rudolph.pienaar@gmail.com',
      url              =   'https://github.com/Chris210634/pman',
      packages         =   ['pman'],
      install_requires =   ['pycurl', 'pyzmq', 'webob', 'pudb', 'psutil', 'docker', 'openshift', 'pfmisc'],
      test_suite       =   'nose.collector',
      tests_require    =   ['nose'],
      scripts          =   ['bin/crunner', 'bin/pfioh', 'bin/pman', 'bin/purl', 'bin/snode'],
      license          =   'MIT',
      zip_safe         =   False
     )
