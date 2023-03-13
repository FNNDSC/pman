"""
Interface between pman and docker engine API.


"""
from pman.abstractmgr import AbstractManager


class SwarmManager(AbstractManager[Unknown]):
    ...
