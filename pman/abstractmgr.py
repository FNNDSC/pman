from abc import ABC, abstractmethod
from typing import Generic, TypeVar, NewType, Optional
from dataclasses import dataclass
from enum import Enum


class ManagerException(Exception):
    def __init__(self, msg, **kwargs):
        self.status_code = kwargs.get('status_code')
        super().__init__(msg)


class JobStatus(Enum):
    notstarted = 'notstarted'
    started = 'started'
    finishedSuccessfully = 'finishedSuccessfully'
    finishedWithError = 'finishedWithError'
    undefined = 'undefined'


JobName = NewType('JobName', str)
Image = NewType('Image', str)


J = TypeVar('J')
"""
``J`` is an object representing a job. Its real type depends
on what is returned by the client library for the specific backend.

Jobs must at least be identifiable by name from the engine.
"""


@dataclass(frozen=True)
class JobInfo:
    name: str
    image: Image
    cmd: str
    timestamp: str
    message: str
    status: JobStatus


class AbstractManager(ABC, Generic[J]):
    """
    An ``AbstractManager`` is an API to a service which can schedule
    (and eventually run) *ChRIS* plugin instances, and maintains persistent
    information about previously scheduled plugin instances.
    """

    def __init__(self, config_dict: dict = None):
        super().__init__()

        self.config = config_dict

    @abstractmethod
    def schedule_job(self, image: Image, command: str, name: JobName,
                     resources_dict: dict, mountdir: Optional[str] = None) -> J:
        """
        Schedule a new job and return the job object.
        """
        ...

    @abstractmethod
    def get_job(self, name: JobName) -> J:
        """
        Get a previously scheduled job object.
        """
        ...

    @abstractmethod
    def get_job_logs(self, job: J) -> str:
        """
        Get the logs string from a previously scheduled job object.
        """
        ...

    @abstractmethod
    def get_job_info(self, job: J) -> JobInfo:
        """
        Get the job's info dictionary for a previously scheduled job object.
        """
        ...

    @abstractmethod
    def remove_job(self, job: J):
        """
        Remove a previously scheduled job.
        """
        ...
