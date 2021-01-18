from os import path
from setuptools import setup

with open(path.join(path.abspath(path.dirname(__file__)), 'README.rst')) as f:
    readme = f.read()

setup(
    name             =   'pman',
    version          =   '2.2.1',
    description      =   'Process Manager',
    long_description =   readme,
    author           =   'Rudolph Pienaar',
    author_email     =   'rudolph.pienaar@gmail.com',
    url              =   'https://github.com/FNNDSC/pman',
    packages         =   ['pman'],
    install_requires =   ['pycurl', 'pyzmq', 'webob', 'pudb', 'psutil', 'docker', 'openshift', 'pfmisc', 'ipaddress', 'fasteners', 'kubernetes', 'python-keystoneclient'],
    test_suite       =   'nose.collector',
    tests_require    =   ['nose'],
    scripts          =   ['bin/pman', 'bin/pman_do'],
    license          =   'MIT',
    zip_safe         =   False,
    python_requires  =   '>=3.6'
)
