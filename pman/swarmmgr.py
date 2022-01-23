"""
Swarm cluster manager module that provides functionality to schedule
jobs (short-lived services) as well as manage their state in the cluster.
"""

import docker
from docker.models.services import Service
from .abstractmgr import AbstractManager, ManagerException, JobStatus, JobInfo, Image, TimeStamp


class SwarmManager(AbstractManager[Service]):

    def __init__(self, config_dict=None):
        super().__init__(config_dict)

        if self.config is None:
            self.docker_client = docker.from_env()
        else:
            self.docker_client = docker.from_env(environment=self.config)

    def schedule_job(self, image, command, name, resources_dict, mountdir=None) -> Service:
        """
        Schedule a new job and return the job (swarm service) object.
        """
        restart_policy = docker.types.RestartPolicy(condition='none')
        mounts = []
        if mountdir is not None:
            mounts.append('%s:/share:rw' % mountdir)
        try:
            job = self.docker_client.services.create(image, command,
                                                     name=name,
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

    def get_job_logs(self, job):
        """
        Get the logs from a previously scheduled job object.
        """
        return ''.join([l.decode() for l in job.logs(stdout=True, stderr=True)])

    def get_job_info(self, job: Service) -> JobInfo:
        """
        Get the job's info for a previously scheduled job object.
        """
        task = self.get_job_task(job)
        if not task:
            return JobInfo(
                name='', image=Image(''), cmd='', timestamp=TimeStamp(''),
                message='task not available yet',
                status=JobStatus.notstarted
            )

        return JobInfo(
            name=job.name,
            image=task['Spec']['ContainerSpec']['Image'],
            cmd=' '.join(task['Spec']['ContainerSpec']['Command']),
            timestamp=TimeStamp(task['Status']['Timestamp']),
            message=task['Status']['Message'],
            status=self.__state2status(task['Status']['State'])
        )

    @staticmethod
    def __state2status(state: str) -> JobStatus:
        if state in ('new', 'pending', 'assigned', 'accepted', 'preparing',
                     'starting'):
            return JobStatus.notstarted
        elif state == 'running':
            return JobStatus.started
        elif state == 'failed':
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
