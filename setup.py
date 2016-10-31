import sys
# Make sure we are running python3
if (sys.version_info[0] < 3) and (sys.version_info[1] < 5):
    sys.exit("Sorry, only Python 3.5+ is supported")

from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(
      name             =   'pman',
      version          =   '0.5',
      description      =   '(Python) Process Manager',
      long_description =   readme(),
      author           =   'Rudolph Pienaar',
      author_email     =   'rudolph.pienaar@gmail.com',
      url              =   'https://github.com/FNNDSC/pman',
      packages         =   ['pman'],
      package_dir      =   {'pman': 'pman'},
      install_requires =   ['pycurl', 'pyzmq', 'webob', 'pudb', 'psutil'],
      test_suite       =   'nose.collector',
      tests_require    =   ['nose'],
      scripts          =   ['bin/pman', 'bin/purl'],
      license          =   'MIT'
     )
