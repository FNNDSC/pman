
from os import path
from setuptools import find_packages, setup

with open(path.join(path.dirname(path.abspath(__file__)), 'README.rst')) as f:
    readme = f.read()

setup(
    name             =   'pman',
    version          =   '3.5.3',
    description      =   'Process Manager',
    long_description =   readme,
    author           =   'FNNDSC Developers',
    author_email     =   'dev@babymri.org',
    url              =   'https://github.com/FNNDSC/pman',
    packages         =   find_packages(),

    install_requires =   ['pudb', 'pfmisc', 'docker', 'openshift', 'kubernetes', 'cromwell-tools',
                          'python-keystoneclient', 'Flask', 'Flask_RESTful', 'environs', 'pyserde',
                          'jinja2'],
    test_suite       =   'nose.collector',
    tests_require    =   ['nose'],
    scripts          =   ['bin/pman'],
    license          =   'MIT',
    zip_safe         =   False,
    python_requires  =   '>=3.8'
)
