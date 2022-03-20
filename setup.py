import os
from setuptools import find_packages, setup


setup(
    name             =   'pman',
    version          =   os.getenv('BUILD_VERSION', 'unknown'),
    description      =   'Process Manager',
    author           =   'FNNDSC Developers',
    author_email     =   'dev@babymri.org',
    url              =   'https://github.com/FNNDSC/pman',
    packages         =   find_packages(),
    install_requires =   ['docker', 'openshift', 'kubernetes', 'cromwell-tools',
                          'python-keystoneclient', 'Flask', 'Flask_RESTful', 'environs',
                          'pyserde', 'jinja2'],
    test_suite       =   'nose.collector',
    tests_require    =   ['nose'],
    license          =   'MIT',
    zip_safe         =   False,
    python_requires  =   '>=3.10.2'
)
