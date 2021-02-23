
from logging.config import dictConfig
from environs import Env

import docker
import logging

logger = logging.getLogger(__name__)


class Config:
    """
    Base configuration
    """
    STATIC_FOLDER = 'static'
    DEBUG = False
    TESTING = False
    SERVER_VERSION = "3.0.0.0"

    def __init__(self):
        self.env = Env()
        self.env.read_env()  # also read .env file, if it exists
        self.STOREBASE = self.env('STOREBASE', None)
        """
        STOREBASE is the real path on the host where data visible to jobs
        will live, and where jobs will write their output data to.
        
        The path given by STOREBASE is typically also mounted by pfioh.
        
        Alternatively, one may give the name of an existing named volume
        (typically managed by docker-compose) via another environment
        variable PMAN_DOCKER_VOLUME. When PMAN_DOCKER_VOLUME is defined
        (and STOREBASE is undefined) the path for that named volume is
        automatically detected and used as the true value for STOREBASE.
        """

        if not self.STOREBASE:
            volume_name = self.env('PMAN_DOCKER_VOLUME')
            if volume_name:
                docker_client = docker.from_env()
                volume = docker_client.volumes.get(volume_name)
                self.STOREBASE = volume.attrs['Mountpoint']
                logger.debug('Given PMAN_DOCKER_VOLUME=%s realized STOREBASE=%s',
                             volume_name, self.STOREBASE)
                # TODO warn if not readable+writable by gid=0


class DevConfig(Config):
    """
    Development configuration
    """
    ENV = 'development'
    DEBUG = True
    TESTING = True

    def __init__(self):
        super().__init__()
        # LOGGING CONFIGURATION
        dictConfig({
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'simple': {
                    'format': '[%(asctime)s] [%(levelname)s]'
                              '[%(module)s:%(lineno)d %(process)d %(thread)d] %(message)s'
                },
            },
            'handlers': {
                'console_simple': {
                    'level': 'INFO',
                    'class': 'logging.StreamHandler',
                    'formatter': 'simple',
                },
                'file': {
                    'level': 'DEBUG',
                    'class': 'logging.FileHandler',
                    'filename': '/tmp/debug.log',
                    'formatter': 'simple'
                }
            },
            'loggers': {
                '': {  # root logger
                    'level': 'INFO',
                    'handlers': ['console_simple'],
                },
                'pman': {  # pman package logger
                    'level': 'DEBUG',
                    'handlers': ['console_simple', 'file'],
                    'propagate': False
                    # required to avoid double logging with root logger
                },
            }
        })

        self.CONTAINER_ENV = 'swarm'


class ProdConfig(Config):
    """
    Production configuration
    """
    ENV = 'production'

    def __init__(self):
        super().__init__()
        # LOGGING CONFIGURATION
        dictConfig({
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'simple': {
                    'format': '[%(asctime)s] [%(levelname)s]'
                              '[%(module)s:%(lineno)d %(process)d %(thread)d] %(message)s'
                },
            },
            'handlers': {
                'console_simple': {
                    'level': 'INFO',
                    'class': 'logging.StreamHandler',
                    'formatter': 'simple',
                },
                'file': {
                    'level': 'DEBUG',
                    'class': 'logging.FileHandler',
                    'filename': '/tmp/debug.log',
                    'formatter': 'simple'
                }
            },
            'loggers': {
                '': {  # root logger
                    'level': 'INFO',
                    'handlers': ['console_simple'],
                },
                'pman': {  # pman package logger
                    'level': 'INFO',
                    'handlers': ['file'],
                    'propagate': False
                },
            }
        })

        # SECURITY WARNING: keep the secret key used in production secret!
        self.SECRET_KEY = self.env('SECRET_KEY')

        self.CONTAINER_ENV = self.env('CONTAINER_ENV')
