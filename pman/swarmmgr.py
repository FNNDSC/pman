"""
Swarm cluster manager module that provides functionality to schedule services as well as
manage their state in the cluster.
"""

import docker
import time


class SwarmManager(object):

    def __init__(self):
        self.docker_client = docker.from_env()

    def schedule(self, image, command, name, restart_policy, mountdir=None):
        """
        Schedule a new service and returns the service object.
        """
        # 'on-failure' restart_policy ensures that the service will not be rescheduled
        # when it completes
        restart_policy = docker.types.RestartPolicy(condition=restart_policy)
        mounts = []
        if mountdir is not None:
            mounts.append('%s:/share:rw' % mountdir)
        return self.docker_client.services.create(image, command, name=name, mounts=mounts,
                                                  restart_policy=restart_policy, tty=True)

    def get_service(self, name):
        """
        Get a previously scheduled service object.
        """
        return self.docker_client.services.get(name)

    def get_service_logs(self, service):
        """
        Get the logs from a previously scheduled service object.
        """
        try:
            return ''.join([l.decode() for l in service.logs(stdout=True, stderr=True)])
        except docker.errors.APIError as e:
            if 'experimental feature' not in str(e):
                raise e
            # We will attempt to get service logs from an old docker engine.
            # In this previous version, service logs ar an experimental feature
            # but we can still get the logs from the service's task's container.

            # At creation, task is not guaranteed to have a container ID yet.
            time.sleep(1)
            task = self.get_service_task(service)
            if 'ContainerID' not in task['Status']['ContainerStatus']:
                return 'not available'  # give up
            container_id = task['Status']['ContainerStatus']['ContainerID']
            container = self.docker_client.containers.get(container_id)
            return container.logs().decode()

    def get_service_task(self, service):
        """
        Get the service's task for a previously scheduled service object.
        """
        tasks = service.tasks()
        return tasks[0] if tasks else None

    def get_service_task_info(self, service):
        """
        Get the service's task info for a previously scheduled service object.
        """
        info = {'id': '', 'image': '', 'cmd': '', 'timestamp': '',
                'message': 'task not available yet', 'status': 'notstarted',
                'containerid': '', 'exitcode': '', 'pid': ''}

        task = self.get_service_task(service)
        if task:
            status = 'undefined'
            state = task['Status']['State']
            if state in ('new', 'pending', 'assigned', 'accepted', 'preparing',
                         'starting'):
                status = 'notstarted'
            elif state == 'running':
                status = 'started'
            elif state == 'failed':
                status = 'finishedWithError'
            elif state == 'complete':
                status = 'finishedSuccessfully'

            info['id'] = task['ID']
            info['image'] = task['Spec']['ContainerSpec']['Image']
            info['cmd'] = ' '.join(task['Spec']['ContainerSpec']['Command'])
            info['timestamp'] = task['Status']['Timestamp']
            info['message'] = task['Status']['Message']
            info['status'] = status

            # observed with docker engine version 1.13.1
            # ContainerID is not immediately available in task status
            info['containerid'] = None
            info['exitcode'] = None
            info['pid'] = None
            if 'ContainerStatus' in task['Status']:
                container_status = task['Status']['ContainerStatus']
                if 'ContainerID' in container_status:
                    info['containerid'] = container_status['ContainerID']
                    if 'ExitCode' in container_status:
                        info['exitcode'] = container_status['ExitCode']
                        info['pid'] = container_status['PID']
                    else:
                        # old docker engine does not supply the exit code and PID to tasks.
                        # We must look it up from the tasks's container.
                        container = self.docker_client.containers.get(info['containerid'])
                        container_status = container.attrs['State']
                        info['exitcode'] = container_status['ExitCode']
                        info['pid'] = container_status['Pid']
        return info

    def remove(self, name):
        """
        Remove a previously scheduled service.
        """
        service = self.get_service(name)
        service.remove()
