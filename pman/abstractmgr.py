
from abc import ABC, abstractmethod


class ManagerException(Exception):
    def __init__(self, msg, **kwargs):
        self.status_code = kwargs.get('status_code')
        super().__init__(msg)


class AbstractManager(ABC):

    def __init__(self, config_dict=None):
        super().__init__()

        self.config = config_dict

    @abstractmethod
    def schedule_job(self, image, command, name, resources_dict, mountdir=None):
        """
        Schedule a new job and return the job object.
        """
        pass

    @abstractmethod
    def get_job(self, name):
        """
        Get a previously scheduled job object.
        """
        pass

    @abstractmethod
    def get_job_logs(self, job):
        """
        Get the logs string from a previously scheduled job object.
        """
        return ''

    @abstractmethod
    def get_job_info(self, job):
        """
        Get the job's info dictionary for a previously scheduled job object.
        """
        job_info = {'name': '', 'image': '', 'cmd': '', 'timestamp': '', 'message': '',
                    'status': ''}
        return job_info

    @abstractmethod
    def remove_job(self, job):
        """
        Remove a previously scheduled job.
        """
        pass
