
from logging.config import dictConfig
from environs import Env
import os


class Config:
    """
    Base configuration
    """
    STATIC_FOLDER = 'static'
    DEBUG = False
    TESTING = False
    SERVER_VERSION = "3.0.0.0"


class DevConfig(Config):
    """
    Development configuration
    """
    ENV = 'development'
    DEBUG = True
    TESTING = True

    def __init__(self):
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

        # Environment variables
        env = Env()
        env.read_env()  # also read .env file, if it exists
        # Allow pman to load env from Openshift manifest. Else, set env as `swarm`
        
        self.CONTAINER_ENV = os.environ.get('CONTAINER_ENV') if os.environ.get('CONTAINER_ENV') is not None \
                             else env('CONTAINER_ENV', 'swarm')
        self.STOREBASE = env('STOREBASE') if self.CONTAINER_ENV == 'swarm' else None


class ProdConfig(Config):
    """
    Production configuration
    """
    ENV = 'production'

    def __init__(self):
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

        # Environment variables-based secrets
        env = Env()
        env.read_env()  # also read .env file, if it exists

        # SECURITY WARNING: keep the secret key used in production secret!
        self.SECRET_KEY = env('SECRET_KEY')

        self.CONTAINER_ENV = env('CONTAINER_ENV')
        self.STOREBASE = env('STOREBASE') if self.CONTAINER_ENV == 'swarm' else None
