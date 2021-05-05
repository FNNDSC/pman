
import os
import logging

from flask import current_app as app
from flask_restful import reqparse, abort, Resource

from .abstractmgr import ManagerException
from .openshiftmgr import OpenShiftManager
from .kubernetesmgr import KubernetesManager
from .swarmmgr import SwarmManager


logger = logging.getLogger(__name__)

parser = reqparse.RequestParser(bundle_errors=True)
parser.add_argument('jid', dest='jid', required=True)
parser.add_argument('cmd_args', dest='cmd_args', required=True)
parser.add_argument('cmd_path_flags', dest='cmd_path_flags')
parser.add_argument('auid', dest='auid', required=True)
parser.add_argument('number_of_workers', dest='number_of_workers', type=int,
                    required=True)
parser.add_argument('cpu_limit', dest='cpu_limit', type=int, required=True)
parser.add_argument('memory_limit', dest='memory_limit', type=int, required=True)
parser.add_argument('gpu_limit', dest='gpu_limit', type=int, required=True)
parser.add_argument('image', dest='image', required=True)
parser.add_argument('selfexec', dest='selfexec', required=True)
parser.add_argument('selfpath', dest='selfpath', required=True)
parser.add_argument('execshell', dest='execshell', required=True)
parser.add_argument('type', dest='type', choices=('ds', 'fs', 'ts'), required=True)


def get_compute_mgr(container_env):
    compute_mgr = None
    if container_env == 'swarm':
        compute_mgr = SwarmManager(app.config)
    elif container_env == 'kubernetes':
        compute_mgr = KubernetesManager(app.config)
    return compute_mgr


class JobListResource(Resource):
    """
    Resource representing the list of jobs scheduled on the compute.
    """

    def __init__(self):
        super(JobListResource, self).__init__()

        # mounting points for the input and outputdir in the app's container!
        self.str_app_container_inputdir = '/share/incoming'
        self.str_app_container_outputdir = '/share/outgoing'

        self.container_env = app.config.get('CONTAINER_ENV')

    def get(self):
        return {
            'server_version': app.config.get('SERVER_VERSION')
        }

    def post(self):
        args = parser.parse_args()
        job_id = args.jid.lstrip('/')

        cmd = self.build_app_cmd(args.cmd_args, args.cmd_path_flags, args.selfpath,
                                 args.selfexec, args.execshell, args.type)

        resources_dict = {'number_of_workers': args.number_of_workers,
                          'cpu_limit': args.cpu_limit,
                          'memory_limit': args.memory_limit,
                          'gpu_limit': args.gpu_limit,
                          }
        share_dir = None
        if app.config.get('STORAGE_TYPE') == 'host':
            storebase = app.config.get('STOREBASE')
            share_dir = os.path.join(storebase, 'key-' + job_id)

        logger.info(f'Scheduling job {job_id} on the {self.container_env} cluster')

        compute_mgr = get_compute_mgr(self.container_env)
        try:
            job = compute_mgr.schedule_job(args.image, cmd, job_id, resources_dict,
                                           share_dir)
        except ManagerException as e:
            logger.error(f'Error from {self.container_env} while scheduling job '
                         f'{job_id}, detail: {str(e)}')
            abort(e.status_code, message=str(e))

        job_info = compute_mgr.get_job_info(job)
        logger.info(f'Successful job {job_id} schedule response from '
                    f'{self.container_env}: {job_info}')
        job_logs = compute_mgr.get_job_logs(job)

        return {
            'jid': job_id,
            'image': job_info['image'],
            'cmd': job_info['cmd'],
            'status': job_info['status'],
            'message': job_info['message'],
            'timestamp': job_info['timestamp'],
            'logs': job_logs
        }, 201

    def build_app_cmd(self, cmd_args, cmd_path_flags, selfpath, selfexec, execshell,
                      plugin_type):
        """
        Build and return the app's cmd string.
        """
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
        outputdir = self.str_app_container_outputdir
        exec = os.path.join(selfpath, selfexec)
        cmd = f'{execshell} {exec}'
        if plugin_type == 'ds':
            inputdir = self.str_app_container_inputdir
            cmd = cmd + f' {cmd_args} {inputdir} {outputdir}'
        elif plugin_type in ('fs', 'ts'):
            cmd = cmd + f' {cmd_args} {outputdir}'
        return cmd


class JobResource(Resource):
    """
    Resource representing a single job scheduled on the compute.
    """
    def __init__(self):
        super(JobResource, self).__init__()

        self.container_env = app.config.get('CONTAINER_ENV')
        self.compute_mgr = get_compute_mgr(self.container_env)

    def get(self, job_id):
        job_id = job_id.lstrip('/')

        logger.info(f'Getting job {job_id} status from the {self.container_env} '
                    f'cluster')
        try:
            job = self.compute_mgr.get_job(job_id)
        except ManagerException as e:
            abort(e.status_code, message=str(e))
        job_info = self.compute_mgr.get_job_info(job)
        logger.info(f'Successful job {job_id} status response from '
                    f'{self.container_env}: {job_info}')
        job_logs = self.compute_mgr.get_job_logs(job)

        return {
            'jid': job_id,
            'image': job_info['image'],
            'cmd': job_info['cmd'],
            'status': job_info['status'],
            'message': job_info['message'],
            'timestamp': job_info['timestamp'],
            'logs': job_logs
        }

    def delete(self, job_id):
        job_id = job_id.lstrip('/')

        logger.info(f'Deleting job {job_id} from {self.container_env}')
        try:
            job = self.compute_mgr.get_job(job_id)
        except ManagerException as e:
            abort(e.status_code, message=str(e))
        self.compute_mgr.remove_job(job)  # remove job from compute cluster
        logger.info(f'Successfully removed job {job_id} from {self.container_env}')
        return '', 204
