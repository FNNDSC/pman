"""
Swarm cluster manager module that provides functionality to schedule services as well as
manage their state in the cluster.
"""

import docker


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
        return ''.join([l.decode() for l in service.logs(stdout=True, stderr=True)])

    def get_service_task(self, service):
        """
        Get the service's task for a previously scheduled service object.
        """
        return service.tasks()[0]

    def get_service_task_info(self, service):
        """
        Get the service's task info for a previously scheduled service object.
        """
        task = self.get_service_task(service)
        status = 'undefined'

        state = task['Status']['State']
        if state in ('new', 'pending', 'assigned', 'accepted', 'preparing', 'starting'):
            status = 'notstarted'
        elif state == 'running':
            status = 'started'
        elif state == 'failed':
            status = 'finishedWithError'
        elif state == 'complete':
            status = 'finishedSuccessfully'

        containerid = ''
        exitcode = ''
        pid = ''
        if 'ContainerStatus' in task['Status']:
            containerid = task['Status']['ContainerStatus']['ContainerID']
            exitcode = task['Status']['ContainerStatus']['ExitCode']
            pid = task['Status']['ContainerStatus']['PID']

        return {'id': task['ID'],
                'image': task['Spec']['ContainerSpec']['Image'],
                'cmd': ' '.join(task['Spec']['ContainerSpec']['Command']),
                'timestamp': task['Status']['Timestamp'],
                'message': task['Status']['Message'],
                'status': status,
                'containerid': containerid,
                'exitcode': exitcode,
                'pid': pid
                }

    def remove(self, name):
        """
        Remove a previously scheduled service.
        """
        service = self.get_service(name)
        service.remove()
