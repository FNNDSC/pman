
from logging.config import dictConfig

from environs import Env

from importlib.metadata import Distribution

from pman._helpers import get_storebase_from_docker

pkg = Distribution.from_name(__package__)


class Config:
    """
    Base configuration
    """
    DEBUG = False
    TESTING = False
    SERVER_VERSION = pkg.version

    def __init__(self):
        # Environment variables
        env = Env()
        env.read_env()  # also read .env file, if it exists

        self.JOB_LOGS_TAIL = env.int('JOB_LOGS_TAIL', 1000)
        self.JOB_LABELS = env.dict('JOB_LABELS', {})
        self.IGNORE_LIMITS = env.bool('IGNORE_LIMITS', False)
        self.CONTAINER_USER = env('CONTAINER_USER', None)
        self.ENABLE_HOME_WORKAROUND = env.bool('ENABLE_HOME_WORKAROUND', False)

        self.CONTAINER_ENV = env('CONTAINER_ENV', 'docker')
        if self.CONTAINER_ENV == 'podman':  # podman is just an alias for docker
            self.CONTAINER_ENV = 'docker'

        default_storage_type = 'docker_local_volume' if self.CONTAINER_ENV == 'docker' else None
        self.STORAGE_TYPE = env('STORAGE_TYPE', default_storage_type)

        self.REMOVE_JOBS = env.bool('REMOVE_JOBS', True)

        if self.STORAGE_TYPE == 'host' or self.STORAGE_TYPE == 'nfs':
            self.STOREBASE = env('STOREBASE')
            if self.STORAGE_TYPE == 'nfs':
                self.NFS_SERVER = env('NFS_SERVER')

        if self.STORAGE_TYPE == 'docker_local_volume':
            pfcon_selector = env('PFCON_SELECTOR', 'org.chrisproject.role=pfcon')
            volume_name = env('VOLUME_NAME', None)
            self.STOREBASE = get_storebase_from_docker(pfcon_selector, volume_name)

        if self.CONTAINER_ENV == 'swarm':
            docker_host = env('DOCKER_HOST', '')
            if docker_host:
                self.DOCKER_HOST = docker_host
            docker_tls_verify = env.int('DOCKER_TLS_VERIFY', None)
            if docker_tls_verify is not None:
                self.DOCKER_TLS_VERIFY = docker_tls_verify
            docker_cert_path = env('DOCKER_CERT_PATH', '')
            if docker_cert_path:
                self.DOCKER_CERT_PATH = docker_cert_path

        if self.CONTAINER_ENV == 'kubernetes':
            self.JOB_NAMESPACE = env('JOB_NAMESPACE', 'default')

        if self.CONTAINER_ENV == 'cromwell':
            self.CROMWELL_URL = env('CROMWELL_URL')
            self.TIMELIMIT_MINUTES = env.int('TIMELIMIT_MINUTES')

        if self.CONTAINER_ENV == 'docker':
            # nothing needs to be done!
            # In the above config code for swarm, docker env variables are intercepted pointlessly.
            # To configure Docker Engine/Podman, use the standard env variables for the Docker client.
            pass

        self.env = env


class DevConfig(Config):
    """
    Development configuration
    """
    ENV = 'development'
    DEBUG = True
    TESTING = True

    def __init__(self):
        super().__init__()

        # DEV LOGGING CONFIGURATION
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
                'console_stdout': {
                    'class': 'logging.StreamHandler',
                    'level': 'DEBUG',
                    'formatter': 'simple',
                    'stream': 'ext://sys.stdout'
                },
            },
            'loggers': {
                '': {  # root logger
                    'level': 'INFO',
                    'handlers': ['console_simple'],
                },
                'pman': {  # pman package logger
                    'level': 'DEBUG',
                    'handlers': ['console_simple', 'console_stdout'],
                    'propagate': False
                    # required to avoid double logging with root logger
                },
            }
        })


class ProdConfig(Config):
    """
    Production configuration
    """
    ENV = 'production'

    def __init__(self):
        super().__init__()

        # PROD LOGGING CONFIGURATION
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
            },
            'loggers': {
                '': {  # root logger
                    'level': 'INFO',
                    'handlers': ['console_simple'],
                },
                'pman': {  # pman package logger
                    'level': 'INFO',
                    'handlers': ['console_simple'],
                    'propagate': False
                },
            }
        })

        # Environment variables-based secrets
        # SECURITY WARNING: keep the secret key used in production secret!
        env = self.env
        self.SECRET_KEY = env('SECRET_KEY')
