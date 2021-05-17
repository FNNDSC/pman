
import os
import logging
import json
import platform
import psutil
import multiprocessing
import socket
import emoji 

from flask import current_app as app
from flask_restful import reqparse, abort, Resource

from .abstractmgr import ManagerException
from .openshiftmgr import OpenShiftManager
from .kubernetesmgr import KubernetesManager
from .swarmmgr import SwarmManager


logger = logging.getLogger(__name__)

parser = reqparse.RequestParser(bundle_errors=True)

parser.add_argument('json',type = str, dest='json', required=False, default='')
parser.add_argument('jid', dest='jid', required=False)
parser.add_argument('cmd_args', dest='cmd_args', required=False)
parser.add_argument('cmd_path_flags', dest='cmd_path_flags', required=False)
parser.add_argument('auid', dest='auid', required=False)
parser.add_argument('number_of_workers', dest='number_of_workers', required=False)
parser.add_argument('cpu_limit', dest='cpu_limit', required=False)
parser.add_argument('memory_limit', dest='memory_limit', required=False)
parser.add_argument('gpu_limit', dest='gpu_limit', required=False)
parser.add_argument('image', dest='image', required=False)
parser.add_argument('selfexec', dest='selfexec', required=False)
parser.add_argument('selfpath', dest='selfpath', required=False)
parser.add_argument('execshell', dest='execshell', required=False)
parser.add_argument('type', dest='type', choices=('ds', 'fs', 'ts'), required=False)




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
        self.openshiftmgr       = None

    def get(self):
        return {
            'server_version': app.config.get('SERVER_VERSION')
        }
        
    def get_openshift_manager(self):
        self.openshiftmgr = OpenShiftManager()
        return self.openshiftmgr
        

    def post(self):
        args = parser.parse_args()

        job_id = args.jid.lstrip('/')

        
        # Declare local variables
        str_image = ''
        number_of_workers=0
        cpu_limit=''
        memory_limit=''
        gpu_limit=0
        
        # Check if a json is passed, then parse each of the json fields 
        # Add condition for additional json fields
        
        if len(args.json) > 0 :
            # json decoding
            json_payload = json.loads(args.json)
        
            if 'jid' in json_payload:
                job_id = json_payload['jid']
                
            if 'cmd_args' in json_payload:
                cmd_args = json_payload['cmd_args']
            
            if 'cmd_path_flags' in json_payload:
                cmd_path_flags = json_payload['cmd_path_flags']
                
            if 'number_of_workers' in json_payload:
                number_of_workers = json_payload['number_of_workers']
                
            if 'auid' in json_payload:
                auid = json_payload['auid']
                
            if 'cpu_limit' in json_payload:
                cpu_limit = json_payload['cpu_limit']
                
            if 'memory_limit' in json_payload:
                memory_limit = json_payload['memory_limit']
                
            if 'gpu_limit' in json_payload:
                gpu_limit = json_payload['gpu_limit']
                
            if 'image' in json_payload:
                image = json_payload['image']
                str_image = image
                
            if 'selfexec' in json_payload:
                selfexec = json_payload['selfexec']
                
            if 'selfpath' in json_payload:
                selfpath = json_payload['selfpath']
                
            if 'execshell' in json_payload:
                execshell = json_payload['execshell']
                
            if 'type' in json_payload:
                type = json_payload['type']
                
            outputdir = self.str_app_container_outputdir
            exec = os.path.join(selfpath, selfexec)
            cmd = f'{execshell} {exec}'
            if type == 'ds':
                inputdir = self.str_app_container_inputdir
                cmd = cmd + f' {cmd_args} {inputdir} {outputdir}'
            elif type in ('fs', 'ts'):
                cmd = cmd + f' {cmd_args} {outputdir}'
                
        else :
            # Parse the arguments from the parameters
                
                
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
            str_image = compute_data['image']
            
        job_logs = ''
        job_info = {'id': '', 'image': '', 'cmd': '', 'timestamp': '', 'message': '',
                    'status': 'undefined', 'containerid': '', 'exitcode': '', 'pid': ''}


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
           
            
        if self.container_env == 'openshift' :
            # If the container env is Openshift
            logger.info(f'Scheduling job {job_id} on the Openshift cluster')
            # Create the Persistent Volume Claim
            if os.environ.get('STORAGE_TYPE') == 'swift':
                self.get_openshift_manager().create_pvc(job_id)
                
            # Set some variables
            incoming_dir = self.str_app_container_inputdir 
            outgoing_dir = self.str_app_container_outputdir
            
            # Ensure that the limits are specified before scheduling a job
            # Remove this if CUBE passes correct limits in future

            cpu_limit = (cpu_limit or compute_data['cpu_limit']) + 'm'
            memory_limit = (memory_limit or compute_data['memory_limit']) + 'Mi'
             
            
            # Schedule the job    
            job = self.get_openshift_manager().schedule_job(str_image, cmd, job_id, \
                                         number_of_workers or compute_data['number_of_workers'],\
                                         cpu_limit,\
                                         memory_limit, \
                                         gpu_limit or compute_data['gpu_limit'], \
                                         incoming_dir, outgoing_dir)
            return {'job_details': str(job)}


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

    
    # Initiate an openshiftmgr instance
    def get_openshift_manager(self):
        self.openshiftmgr = OpenShiftManager()
        return self.openshiftmgr
        
    # Get the status of a running jon on Openshift
    def t_status_process_openshift(self, jid):
        """
        Determine the status of a job scheduled using the openshift manager.
        PRECONDITIONS:
        o   Only call this method if a container structure exists
            in the relevant job tree!
        POSTCONDITIONS:
        o   If the job is completed, then shutdown the container cluster
            service.
        """
        
        str_logs = ''
        # Get job-id from request
        #jid = self.jid

        # Query OpenShift API to get job state
        d_json  = self.get_openshift_manager().state(jid)
        
        print (d_json)
        print (jid)

        if d_json['Status']['Message'] == 'finished':
            pod_names = self.get_openshift_manager().get_pod_names_in_job(jid)
            for _, pod_name in enumerate(pod_names):
                str_logs += self.get_openshift_manager().get_job_pod_logs(pod_name, jid)
        else:
            str_logs = d_json['Status']['Message']

        status  = d_json['Status']
        currentState =  d_json['Status']['Message']

        return {
            'status':           status,
            'logs':             str_logs,
            'currentState':     [currentState]
        }
            
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
                
        if container_env == 'openshift':
            logger.info(f'Getting job {job_id} status from the Openshift cluster')
            try:
                d_containerStatus       =   self.t_status_process_openshift(job_id)
                status                  =   d_containerStatus['status']
                logs                    =   d_containerStatus['logs']
                currentState            =   d_containerStatus['currentState']
            except Exception as e:
                if isinstance(e, ApiException) and e.reason == 'Not Found':
                    status = logs = currentState = e.reason
                else:
                    raise e

            d_ret = {
                'description':   str(status),
                'l_logs':     str(logs),
                'l_status': currentState
            }
            if 'finished' in str(currentState) :
                job_status = 'finishedSuccessfully'
                
                # Also delete the job pod and related pvc
                try:
                    job = self.get_openshift_manager().get_job(job_id)
                    self.get_openshift_manager().remove_pvc(job_id)
                    self.get_openshift_manager().remove_job(job_id)
                except Exception as err:
                    logger.info(f'Error deleting pvc/job: {err}')
                    
            else :
                job_status = str(currentState)
                
            return {
                    'jid': job_id,
                    'image': '',
                    'cmd': '',
                    'status': job_status,
                    'message': str(status),
                    'timestamp': '',
                    'containerid': '',
                    'exitcode': '0',
                    'pid': '0',
                    'logs': str(logs)

            }



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

        
class Hello(Resource):

     # Respond to simple 'hello' requests from the server
    def get(self):
   
            container_env = app.config.get('CONTAINER_ENV')

            smiling_face = emoji.emojize(":grinning_face_with_big_eyes:")
            logger.info(f'pman says hello from {container_env} {smiling_face}')
            b_status            = False
            d_ret               = {}
            d_ret['message']                = (f'pman says hello from {container_env} {smiling_face}')
            d_ret['sysinfo']                = {}
            d_ret['sysinfo']['system']      = platform.system()
            d_ret['sysinfo']['machine']     = platform.machine()
            d_ret['sysinfo']['platform']    = platform.platform()
            d_ret['sysinfo']['uname']       = platform.uname()
            d_ret['sysinfo']['version']     = platform.version()
            d_ret['sysinfo']['memory']      = psutil.virtual_memory()
            d_ret['sysinfo']['cpucount']    = multiprocessing.cpu_count()
            d_ret['sysinfo']['loadavg']     = os.getloadavg()
            d_ret['sysinfo']['cpu_percent'] = psutil.cpu_percent()
            d_ret['sysinfo']['hostname']    = socket.gethostname()
            d_ret['sysinfo']['inet']        = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]
            b_status                        = True
            
            return { 'd_ret':   d_ret,
                 'status':  b_status}
                 

