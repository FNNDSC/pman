
import os
import logging
from typing import List, Collection, Literal

from flask import current_app as app
from flask_restful import reqparse, abort, Resource

from .abstractmgr import ManagerException
from .openshiftmgr import OpenShiftManager
from .kubernetesmgr import KubernetesManager
from .swarmmgr import SwarmManager
from .cromwellmgr import CromwellManager

logger = logging.getLogger(__name__)

parser = reqparse.RequestParser(bundle_errors=True)
parser.add_argument('jid', dest='jid', required=True,type = str)
parser.add_argument('args', dest='args', type=list, location='json', required=True)
parser.add_argument('args_path_flags', dest='args_path_flags', type=frozenset,
                    location='json', required=False, default=frozenset())
parser.add_argument('auid', dest='auid', required=True)
parser.add_argument('number_of_workers', dest='number_of_workers', type=int,
                    required=True)
parser.add_argument('cpu_limit', dest='cpu_limit', type=int, required=True)
parser.add_argument('memory_limit', dest='memory_limit', type=int, required=True)
parser.add_argument('gpu_limit', dest='gpu_limit', type=int, required=True)
parser.add_argument('image', dest='image', required=True)
parser.add_argument('entrypoint', dest='entrypoint', type=list, location='json',
                    required=True)
parser.add_argument('type', dest='type', choices=('ds', 'fs', 'ts'), required=True)
parser.add_argument('env', dest='env', type=list, location='json', default=[])


def get_compute_mgr(container_env):
    compute_mgr = None
    if container_env == 'swarm':
        compute_mgr = SwarmManager(app.config)
    elif container_env == 'kubernetes':
        compute_mgr = KubernetesManager(app.config)
    elif container_env == 'openshift':
        compute_mgr = OpenShiftManager()
    elif container_env == 'cromwell':
        compute_mgr = CromwellManager(app.config)
    return compute_mgr


class JobListResource(Resource):
    """
    Resource representing the list of jobs scheduled on the compute.
    """

    def __init__(self):
        super(JobListResource, self).__init__()
        self.container_env = app.config.get('CONTAINER_ENV')

    def get(self):
        return {
            'server_version': app.config.get('SERVER_VERSION')
        }

    def post(self):
        args = parser.parse_args()

        if len(args.entrypoint) == 0:
            abort(400, message='"entrypoint" cannot be empty')

        for s in args.env:
            if len(s.split('=', 1)) != 2:
                abort(400, message='"env" must be a list of "key=value" strings')

        job_id = args.jid.lstrip('/')
        logger.info(f'Scheduling job {job_id} on the {self.container_env} cluster')
        
        cmd = self.build_app_cmd(args.args, args.args_path_flags, args.entrypoint, args.type, job_id)
        logger.info(f'command: {cmd}')
        resources_dict = {'number_of_workers': args.number_of_workers,
                          'cpu_limit': args.cpu_limit,
                          'memory_limit': args.memory_limit,
                          'gpu_limit': args.gpu_limit,
                          }
        # if storage_type in ('host', 'nfs'):
        #     storebase = app.config.get('STOREBASE')
        #     share_dir = os.path.join(storebase, 'key-' + job_id)
        

        compute_mgr = get_compute_mgr(self.container_env)
        try:
            job = compute_mgr.schedule_job(args.image, cmd, job_id, resources_dict,
                                           args.env)
        except ManagerException as e:
            logger.error(f'Error from {self.container_env} while scheduling job '
                         f'{job_id}, detail: {str(e)}')
            abort(e.status_code, message=str(e))

        job_info = compute_mgr.get_job_info(job)
        logger.info(f'Successful job {job_id} schedule response from '
                    f'{self.container_env}: {job_info}')
        job_logs = ''

        return {
            'jid': job_id,
            'image': job_info.image,
            'cmd': job_info.cmd,
            'status': job_info.status.value,
            'message': job_info.message,
            'timestamp': job_info.timestamp,
            'logs': job_logs
        }, 201

    def build_app_cmd(
            self,
            args: List[str],
            args_path_flags: Collection[str],
            entrypoint: List[str],
            plugin_type: Literal['ds', 'fs', 'ts'],
            job_id: str
    ) -> List[str]:
        input_dir = f'/share/key-{job_id}/incoming'
        output_dir = f'/share/key-{job_id}/outgoing'
        cmd = entrypoint + localize_path_args(args, args_path_flags, input_dir)
        if plugin_type == 'ds':
            cmd.append(input_dir)
        cmd.append(output_dir)
        return cmd


class JobResource(Resource):
    """
    Resource representing a single job scheduled on the compute.
    """
    def __init__(self):
        super(JobResource, self).__init__()

        self.container_env = app.config.get('CONTAINER_ENV')
        self.compute_mgr = get_compute_mgr(self.container_env)
        self.job_logs_tail = app.config.get('JOB_LOGS_TAIL')

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
        job_logs = self.compute_mgr.get_job_logs(job, self.job_logs_tail)
        if isinstance(job_logs, bytes):
            job_logs = job_logs.decode(encoding='utf-8', errors='replace')

        return {
            'jid': job_id,
            'image': job_info.image,
            'cmd': job_info.cmd,
            'status': job_info.status.value,
            'message': job_info.message,
            'timestamp': job_info.timestamp,
            'logs': job_logs
        }

    def delete(self, job_id):
        if not app.config.get('REMOVE_JOBS'):
            logger.info(f'Deletion request for job {job_id}, '
                        'doing nothing because config.REMOVE_JOBS=no')
            return '', 204

        job_id = job_id.lstrip('/')

        logger.info(f'Deleting job {job_id} from {self.container_env}')
        try:
            job = self.compute_mgr.get_job(job_id)
        except ManagerException as e:
            abort(e.status_code, message=str(e))
        self.compute_mgr.remove_job(job)  # remove job from compute cluster
        logger.info(f'Successfully removed job {job_id} from {self.container_env}')
        return '', 204


def localize_path_args(args: List[str], path_flags: Collection[str], input_dir: str) -> List[str]:
    """
    Replace the strings following path flags with the input directory.

    https://github.com/FNNDSC/CHRIS_docs/blob/7ac85e9ae1070947e6e2cda62747b427028229b0/SPEC.adoc#path-arguments
    """
    if len(args) == 0:
        return args
    if args[0] in path_flags:
        return [args[0], input_dir] + localize_path_args(args[2:], path_flags, input_dir)
    return args[0:1] + localize_path_args(args[1:], path_flags, input_dir)
