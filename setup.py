#/usr/bin/env python

from distutils.core import setup

setup(
      name             =   'pman',
      version          =   '0.1',
      description      =   '(Python) Process Manager',
      author           =   'Rudolph Pienaar',
      author_email     =   'rudolph.pienaar@gmail.com',
      url              =   'https://github.com/FNNDSC/pman',
      packages         =   ['pman'],
      package_dir      =   {'pman': 'pman'},
      install_requires =   ['pycurl', 'pyzmq', 'webob'],
      license          =   'MIT'
     )
