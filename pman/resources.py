
import os
import logging

from flask import request, current_app as app
from flask_restful import reqparse, abort, Resource

from kubernetes.client.rest import ApiException
import docker

from .openshiftmgr import OpenShiftManager
from .swarmmgr import SwarmManager


logger = logging.getLogger(__name__)

parser = reqparse.RequestParser(bundle_errors=True)
parser.add_argument('jid', dest='jid', required=True)
parser.add_argument('cmd_args', dest='cmd_args', required=True)
parser.add_argument('cmd_path_flags', dest='cmd_path_flags')
parser.add_argument('auid', dest='auid', required=True)
parser.add_argument('number_of_workers', dest='number_of_workers', required=True,)
parser.add_argument('cpu_limit', dest='cpu_limit', required=True)
parser.add_argument('memory_limit', dest='memory_limit', required=True)
parser.add_argument('gpu_limit', dest='gpu_limit', required=True)
parser.add_argument('image', dest='image', required=True)
parser.add_argument('selfexec', dest='selfexec', required=True)
parser.add_argument('selfpath', dest='selfpath', required=True)
parser.add_argument('execshell', dest='execshell', required=True)
parser.add_argument('type', dest='type', choices=('ds', 'fs', 'ts'), required=True)


class JobList(Resource):
    """
    Resource representing the list of jobs running on the compute.
    """

    def __init__(self):
        super(JobList, self).__init__()

        # mounting points for the input and outputdir in the app's container!
        self.str_app_container_inputdir = '/share/incoming'
        self.str_app_container_outputdir = '/share/outgoing'

        self.container_env = app.config.get('CONTAINER_ENV')

    def get(self):
        return {
            'server_version': app.config.get('SERVER_VERSION'),
        }

    def post(self):
        args = parser.parse_args()

        job_id = args.jid.lstrip('/')
        compute_data = {
            'cmd_args': args.cmd_args,
            'cmd_path_flags': args.cmd_path_flags,
            'auid': args.auid,
            'number_of_workers': args.number_of_workers,
            'cpu_limit': args.cpu_limit,
            'memory_limit': args.memory_limit,
            'gpu_limit': args.gpu_limit,
            'image': args.image,
            'selfexec': args.selfexec,
            'selfpath': args.selfpath,
            'execshell': args.execshell,
            'type': args.type,
        }
        cmd = self.build_app_cmd(compute_data)
        job_logs = ''
        job_info = {'id': '', 'image': '', 'cmd': '', 'timestamp': '', 'message': '',
                    'status': 'undefined', 'containerid': '', 'exitcode': '', 'pid': ''}

        if self.container_env == 'swarm':
            storebase = app.config.get('STOREBASE')
            share_dir = os.path.join(storebase, 'key-' + job_id)

            swarm_mgr = SwarmManager()
            logger.info(f'Scheduling job {job_id} on the Swarm cluster')
            try:
                service = swarm_mgr.schedule(compute_data['image'], cmd, job_id, 'none',
                                             share_dir)
            except docker.errors.APIError as e:
                logger.error(f'Error from Swarm while scheduling job {job_id}, detail: '
                             f'{str(e)}')
                status_code = e.response.status_code
                status_code = 503 if status_code == 500 else status_code
                abort(status_code, message=str(e))
            job_info = swarm_mgr.get_service_task_info(service)
            logger.info(f'Successful job {job_id} schedule response from Swarm: '
                        f'{job_info}')
            job_logs = swarm_mgr.get_service_logs(service)

        return {
            'jid': job_id,
            'image': job_info['image'],
            'cmd': job_info['cmd'],
            'status': job_info['status'],
            'message': job_info['message'],
            'timestamp': job_info['timestamp'],
            'containerid': job_info['containerid'],
            'exitcode': job_info['exitcode'],
            'pid': job_info['pid'],
            'logs': job_logs
        }

    def build_app_cmd(self, compute_data):
        """
        Build and return the app's cmd string.
        """
        cmd_args = compute_data['cmd_args']
        cmd_path_flags = compute_data['cmd_path_flags']
        if cmd_path_flags:
            # process the argument of any cmd flag that is a 'path'
            path_flags = cmd_path_flags.split(',')
            args = cmd_args.split()
            for i in range(len(args) - 1):
                if args[i] in path_flags:
                    # each flag value is a string of one or more paths separated by comma
                    # paths = args[i+1].split(',')
                    # base_inputdir = self.str_app_container_inputdir
                    # paths = [os.path.join(base_inputdir, p.lstrip('/')) for p in paths]
                    # args[i+1] = ','.join(paths)

                    # the next is tmp until CUBE's assumptions about inputdir and path
                    # parameters are removed
                    args[i+1] = self.str_app_container_inputdir
            cmd_args = ' '.join(args)
        selfpath = compute_data['selfpath']
        selfexec = compute_data['selfexec']
        execshell = compute_data['execshell']
        type = compute_data['type']
        outputdir = self.str_app_container_outputdir
        exec = os.path.join(selfpath, selfexec)
        cmd = f'{execshell} {exec}'
        if type == 'ds':
            inputdir = self.str_app_container_inputdir
            cmd = cmd + f' {cmd_args} {inputdir} {outputdir}'
        elif type in ('fs', 'ts'):
            cmd = cmd + f' {cmd_args} {outputdir}'
        return cmd


class Job(Resource):
    """
    Resource representing a single job running on the compute.
    """
    def get(self, job_id):
        container_env = app.config.get('CONTAINER_ENV')
        job_logs = ''
        job_info = {'id': '', 'image': '', 'cmd': '', 'timestamp': '', 'message': '',
                    'status': 'undefined', 'containerid': '', 'exitcode': '', 'pid': ''}

        if container_env == 'swarm':
            swarm_mgr = SwarmManager()
            logger.info(f'Getting job {job_id} status from the Swarm cluster')
            try:
                service = swarm_mgr.get_service(job_id)
            except docker.errors.NotFound as e:
                abort(404, message=str(e))
            except docker.errors.APIError as e:
                status_code = e.response.status_code
                status_code = 503 if status_code == 500 else status_code
                abort(status_code, message=str(e))
            except docker.errors.InvalidVersion as e:
                abort(400, message=str(e))
            job_info = swarm_mgr.get_service_task_info(service)
            logger.info(f'Successful job {job_id} status response from Swarm: '
                        f'{job_info}')
            job_logs = swarm_mgr.get_service_logs(service)

            if job_info['status'] in ('undefined', 'finishedWithError',
                                      'finishedSuccessfully'):
                service.remove()  # remove job from swarm cluster

        return {
            'jid': job_id,
            'image': job_info['image'],
            'cmd': job_info['cmd'],
            'status': job_info['status'],
            'message': job_info['message'],
            'timestamp': job_info['timestamp'],
            'containerid': job_info['containerid'],
            'exitcode': job_info['exitcode'],
            'pid': job_info['pid'],
            'logs': job_logs
        }
