import shlex
import logging
from typing import AnyStr, List, Optional

import docker
from docker import DockerClient
from docker.models.containers import Container
from docker.types import DeviceRequest

from pman.abstractmgr import (AbstractManager, Image, JobInfo, JobName,
                              JobStatus, ManagerException, MountsDict,
                              ResourcesDict, TimeStamp)


logger = logging.getLogger(__name__)


class DockerManager(AbstractManager[Container]):
    """
    Interface between pman and Docker Engine or Podman API.
    """
    def __init__(self, config_dict=None, docker_client: DockerClient = None):
        super().__init__(config_dict)

        # these should be part of the AbstractManager.schedule_job signature,
        # but I'm putting it here to keep the PR diff small
        self.job_labels = config_dict.get('JOB_LABELS')
        self.ignore_limits = config_dict.get('IGNORE_LIMITS')

        if docker_client is not None:
            self.__docker = docker_client
        else:
            self.__docker = docker.from_env()

    def schedule_job(self, image: Image, command: List[str], name: JobName,
                     resources_dict: ResourcesDict, env: List[str], uid: Optional[int],
                     gid: Optional[int], mounts_dict: MountsDict) -> Container:

        if resources_dict['number_of_workers'] != 1:
            raise ManagerException(
                'Compute environment only supports number_of_workers=1, '
                'got number_of_workers=' + str(resources_dict['number_of_workers']),
                status_code=400
            )

        volumes = {
            'volumes': {
                mounts_dict['inputdir_source']: {'bind': mounts_dict['inputdir_target'],
                                                 'mode': 'ro'},
                mounts_dict['outputdir_source']: {'bind': mounts_dict['outputdir_target'],
                                                  'mode': 'rw'},
            }
        }

        limits = {}
        if not self.ignore_limits:
            limits['nano_cpus'] = int(resources_dict['cpu_limit'] * 1e6)
            limits['mem_reservation'] = resources_dict['memory_limit'] * 1024 * 1024

        if resources_dict['gpu_limit'] > 0:
            limits['device_requests'] = [
                DeviceRequest(count=resources_dict['gpu_limit'], capabilities=[['gpu']])
            ]

        user_spec = {}
        if uid is not None:
            user_spec['user'] = uid
        if gid is not None:
            user_spec['group_add'] = [gid]

        shm_size = {}
        if (s := self.config.get('SHM_SIZE')) is not None:
            shm_size['shm_size'] = s.as_mb()

        # Docker networks configuration
        networks = {}
        if docker_network := self.config.get('DOCKER_NETWORKS'):
            networks['network'] = docker_network

        logger.debug(f"networks: {networks}")

        container = self.__docker.containers.run(
            image=image,
            command=command,
            name=name,
            environment=env,
            restart_policy = {'Name': 'no', 'MaximumRetryCount': 0},
            detach=True,
            labels=self.job_labels,
            **limits,
            **user_spec,
            **shm_size,
            **volumes,
            **networks
        )

        return container

    def get_job(self, name: JobName) -> Container:
        try:
            return self.__docker.containers.get(name)
        except docker.errors.NotFound as e:
            raise ManagerException(str(e), status_code=404)

    def get_job_logs(self, job: Container, tail: int) -> AnyStr:
        return job.logs(stdout=True, stderr=True, tail=tail)

    def get_job_info(self, job: Container) -> JobInfo:
        return JobInfo(
            name=JobName(job.name),
            image=Image(job.attrs['Config']['Image']),
            cmd=shlex.join(job.attrs['Config']['Cmd']),
            timestamp=_get_timestamp_from(job),
            message=job.attrs['State']['Status'],
            status=_get_status_from(job)
        )

    def remove_job(self, job: Container):
        job.remove(force=True)


def _get_timestamp_from(c: Container) -> TimeStamp:
    state = c.attrs['State']
    if state['FinishedAt'] != '0001-01-01T00:00:00Z':
        return state['FinishedAt']
    return state['StartedAt']


def _get_status_from(c: Container) -> JobStatus:
    # see https://docs.docker.com/engine/api/v1.42/#tag/Container/operation/ContainerInspect
    state = c.attrs['State']
    if state['Running'] or state['Paused']:
        return JobStatus.started
    if state['Status'] == 'created':
        return JobStatus.notstarted
    if state['OOMKilled'] or state['Dead']:
        return JobStatus.finishedWithError
    if state['Status'] == 'exited':
        if state['ExitCode'] == 0:
            return JobStatus.finishedSuccessfully
        return JobStatus.finishedWithError
    return JobStatus.undefined
