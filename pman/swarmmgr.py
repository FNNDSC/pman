"""
Swarm cluster manager module that provides functionality to schedule
jobs (short-lived services) as well as manage their state in the cluster.
"""
from typing import AnyStr, Sequence, Iterable

import docker
from docker.models.services import Service
from .abstractmgr import (AbstractManager, ManagerException, JobStatus, JobInfo, Image,
                          TimeStamp, JobName)


class SwarmManager(AbstractManager[Service]):

    def __init__(self, config_dict=None):
        super().__init__(config_dict)

        if self.config is None:
            self.docker_client = docker.from_env()
        else:
            self.docker_client = docker.from_env(environment=self.config)

    def schedule_job(self, image, command, name, resources_dict, env, uid, gid,
                     mounts_dict) -> Service:
        """
        Schedule a new job and return the job (swarm service) object.
        """
        restart_policy = docker.types.RestartPolicy(condition='none')
        mounts = [f'{mounts_dict["inputdir_source"]}:{mounts_dict["inputdir_target"]}:ro',
                  f'{mounts_dict["outputdir_source"]}:{mounts_dict["outputdir_target"]}:rw']
        try:
            job = self.docker_client.services.create(image, command,
                                                     name=name,
                                                     env=env,
                                                     mounts=mounts,
                                                     restart_policy=restart_policy,
                                                     tty=True)
        except docker.errors.APIError as e:
            status_code = 503 if e.response.status_code == 500 else e.response.status_code
            raise ManagerException(str(e), status_code=status_code)
        return job

    def get_job(self, name) -> Service:
        """
        Get a previously scheduled job object.
        """
        try:
            job = self.docker_client.services.get(name)
        except docker.errors.NotFound as e:
            raise ManagerException(str(e), status_code=404)
        except docker.errors.APIError as e:
            status_code = 503 if e.response.status_code == 500 else e.response.status_code
            raise ManagerException(str(e), status_code=status_code)
        except docker.errors.InvalidVersion as e:
            raise ManagerException(str(e), status_code=400)
        return job

    def get_job_logs(self, job: Service, tail: int) -> AnyStr:
        return b''.join(job.logs(stdout=True, stderr=True, tail=tail))

    def get_job_info(self, job: Service) -> JobInfo:
        """
        Get the job's info for a previously scheduled job object.
        """
        task = self.get_job_task(job)
        if not task:
            return JobInfo(
                name=JobName(''), image=Image(''), cmd='', timestamp=TimeStamp(''),
                message='task not available yet',
                status=JobStatus.notstarted
            )

        return JobInfo(
            name=JobName(job.name),
            image=task['Spec']['ContainerSpec']['Image'],
            cmd=' '.join(task['Spec']['ContainerSpec']['Command']),
            timestamp=TimeStamp(task['Status']['Timestamp']),
            message=self.__get_message_from(task),
            status=self.__state2status(task['Status']['State'])
        )

    @classmethod
    def __get_message_from(cls, task: dict) -> str:
        if cls.__was_oom_killed(task):
            return 'shutdown by docker swarm (out of memory)'
        return task['Status']['Message']

    @staticmethod
    def __was_oom_killed(task: dict) -> bool:
        return task['Status']['State'] == 'shutdown' and task['Status']['ContainerStatus']['ExitCode'] == 137

    @staticmethod
    def __state2status(state: str) -> JobStatus:
        """
        Documentation: https://docs.docker.com/engine/api/v1.41/#tag/Task/operation/TaskList

        State is one of:

         Enum: "new" "allocated" "pending" "assigned" "accepted" "preparing" "ready" "starting"
         "running" "complete" "shutdown" "failed" "rejected" "remove" "orphaned"
        """
        if state in ('new', 'allocated', 'pending', 'assigned', 'accepted', 'preparing',
                     'ready', 'starting'):
            return JobStatus.notstarted
        elif state == 'running':
            return JobStatus.started
        elif state in ('failed', 'shutdown'):
            return JobStatus.finishedWithError
        elif state == 'complete':
            return JobStatus.finishedSuccessfully
        return JobStatus.undefined

    def remove_job(self, job):
        """
        Remove a previously scheduled job.
        """
        job.remove()

    def get_job_task(self, job):
        """
        Get the job's task for a previously scheduled job object.
        """
        tasks = job.tasks()
        return tasks[0] if tasks else None
