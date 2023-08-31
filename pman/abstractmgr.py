from abc import ABC, abstractmethod
from typing import Generic, TypeVar, NewType, Optional, TypedDict, AnyStr, List
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
"""An identifying string which ``pman`` can be queried for to retrieve a submitted job."""
Image = NewType('Image', str)
"""An OCI container image tag, e.g. ``docker.io/fnndsc/pl-simpledsapp:2.0.1``"""
TimeStamp = NewType('TimeStamp', str)
"""A time and date in ISO format."""

J = TypeVar('J')
"""
``J`` is an object representing a job. Its real type depends
on what is returned by the client library for the specific backend.

Jobs must at least be identifiable by name from the engine.
"""


@dataclass(frozen=True)
class JobInfo:
    name: JobName
    """A name which ``pman`` can be queried for to retrieve this job."""
    image: Image
    cmd: str
    timestamp: TimeStamp
    """Time of completion."""
    message: str
    status: JobStatus


class ResourcesDict(TypedDict):
    number_of_workers: int
    """
    Number of workers for multi-node parallelism.
    """
    cpu_limit: int
    """
    CPU resource in millicores.
    
    For example, 1000 represents "1000m" or 1.0 CPU cores.
    
    https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-cpu
    """
    memory_limit: int
    """
    Memory requirement in mebibytes.
    
    For example, 1000 represents "1000Mi" = "1049M" = 1.049e+9 bytes
    """
    gpu_limit: int
    """
    GPU requirement in number of GPUs.
    """


class MountsDict(TypedDict):
    inputdir_source: str
    """
    Absolute path to the source input directory or otherwise a volume name.
    """
    inputdir_target: str
    """
    Absolute path to the target input directory (within the container).
    """
    outputdir_source: str
    """
    Absolute path to the source output directory or otherwise a volume name.
    """
    outputdir_target: str
    """
    Absolute path to the target output directory (within the container).
    """


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
    def schedule_job(self, image: Image, command: List[str], name: JobName,
                     resources_dict: ResourcesDict, env: List[str],
                     uid: Optional[int], gid: Optional[int],
                     mounts_dict: MountsDict) -> J:
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
    def get_job_logs(self, job: J, tail: int) -> AnyStr:
        """
        Get the logs (combined stdout+stdin) from a previously scheduled job object.

        :param job: the job which to get the logs for
        :param tail: how many bytes to read from the end of the logs.
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
