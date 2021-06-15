"""
Kubernetes cluster manager module that provides functionality to schedule jobs as well
as manage their state in the cluster.
"""

from kubernetes import client as k_client
from kubernetes import config as k_config
from kubernetes.client.rest import ApiException
from .abstractmgr import AbstractManager, ManagerException


class KubernetesManager(AbstractManager):

    def __init__(self, config_dict=None):
        super().__init__(config_dict)

        k_config.load_incluster_config()
        self.kube_client = k_client.CoreV1Api()
        self.kube_v1_batch_client = k_client.BatchV1Api()

    def schedule_job(self, image, command, name, resources_dict, mountdir=None):
        """
        Schedule a new job and return the job object.
        """
        job_instance = self.create_job(image, command, name, resources_dict, mountdir)
        job = self.submit_job(job_instance)
        return job

    def get_job(self, name):
        """
        Get a previously scheduled job object.
        """
        job_namespace = self.config.get('JOB_NAMESPACE')
        try:
            job = self.kube_v1_batch_client.read_namespaced_job(name, job_namespace)
        except ApiException as e:
            status_code = 503 if e.status == 500 else e.status
            raise ManagerException(str(e), status_code=status_code)
        return job

    def get_job_logs(self, job):
        """
        Get the logs string from a previously scheduled job object.
        """
        # TODO: Think of a better way to abstract out logs in case of multiple pods running parallelly

        logs = ''
        pods = self.get_job_pods(job.metadata.name)
        for pod_item in pods.items:
            pod_name = pod_item.metadata.name
            logs += self.get_pod_log(pod_name)
        return logs

    def get_job_info(self, job):
        """
        Get the job's info dictionary for a previously scheduled job object.
        """
        info = super().get_job_info(job)
        status = 'notstarted'
        message = 'task not available yet'
        conditions = job.status.conditions
        failed = job.status.failed
        succeeded = job.status.succeeded
        completion_time = job.status.completion_time

        if not (conditions is None and failed is None and succeeded is None):
            if conditions:
                for condition in conditions:
                    if condition.type == 'Failed' and condition.status == 'True':
                        message = condition.message
                        status = 'finishedWithError'
                        break
            if status == 'notstarted':
                if completion_time and succeeded:
                    message = 'finished'
                    status = 'finishedSuccessfully'
                elif job.status.active:
                    message = 'running'
                    status = 'started'
                else:
                    message = 'inactive'
                    status = 'undefined'

        info['name'] = job.metadata.name
        info['image'] = job.spec.template.spec.containers[0].image
        info['cmd'] = ' '.join(job.spec.template.spec.containers[0].command)
        if completion_time is not None:
            info['timestamp'] = completion_time.isoformat()
        info['message'] = message
        info['status'] = status
        return info

    def remove_job(self, job):
        """
        Remove a previously scheduled job.
        """
        job_namespace = self.config.get('JOB_NAMESPACE')
        body = k_client.V1DeleteOptions(propagation_policy='Background')
        self.kube_v1_batch_client.delete_namespaced_job(job.metadata.name, body=body,
                                                        namespace=job_namespace)

    def create_job(self, image, command, name, resources_dict, mountdir=None):
        """
        Create and return a new job instance.
        """
        number_of_workers = resources_dict.get('number_of_workers')
        cpu_limit = str(resources_dict.get('cpu_limit')) + 'm'
        memory_limit = str(resources_dict.get('memory_limit')) + 'Mi'
        gpu_limit = resources_dict.get('gpu_limit')

        # configure pod's containers
        requests = {'memory': '150Mi', 'cpu': '250m'}
        limits = {'memory': memory_limit, 'cpu': cpu_limit}
        env = []
        if gpu_limit > 0:
            # ref: https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/
            limits['nvidia.com/gpu'] = gpu_limit
            env = [k_client.V1EnvVar(name='NVIDIA_VISIBLE_DEVICES', value='all'),
                   k_client.V1EnvVar(name='NVIDIA_DRIVER_CAPABILITIES',
                                     value='compute,utility'),
                   k_client.V1EnvVar(name='NVIDIA_REQUIRE_CUDA', value='cuda>=9.0')],
        container = k_client.V1Container(
            name=name,
            image=image,
            env=env,
            command=command.split(' '),
            security_context=k_client.V1SecurityContext(
                allow_privilege_escalation=False,
                capabilities=k_client.V1Capabilities(drop=['ALL'])
            ),
            resources=k_client.V1ResourceRequirements(limits=limits, requests=requests),
            volume_mounts=[k_client.V1VolumeMount(mount_path='/share',
                                                  name='storebase')]
        )
        # configure pod template's spec
        storage_type = self.config.get('STORAGE_TYPE')
        if storage_type == 'host':
            volume = k_client.V1Volume(
                name='storebase',
                host_path=k_client.V1HostPathVolumeSource(path=mountdir)
            )
        else:
            volume = k_client.V1Volume(
                name='storebase',
                nfs=k_client.V1NFSVolumeSource(server=self.config.get('NFS_SERVER'),
                                               path=mountdir)
            )
        template = k_client.V1PodTemplateSpec(
            spec=k_client.V1PodSpec(restart_policy='Never',
                                    containers=[container],
                                    volumes=[volume])
        )
        # configure job's spec
        spec = k_client.V1JobSpec(
            parallelism=number_of_workers,
            completions=number_of_workers,
            backoff_limit=1,
            ttl_seconds_after_finished=86400,  # 24h
            active_deadline_seconds=43200,  # 12h
            template=template
        )
        # instantiate the job object
        job = k_client.V1Job(
            api_version='batch/v1',
            kind='Job',
            metadata=k_client.V1ObjectMeta(name=name),
            spec=spec)
        return job

    def submit_job(self, job):
        """
        Submit a new job and return the job object.
        """
        job_namespace = self.config.get('JOB_NAMESPACE')
        try:
            job = self.kube_v1_batch_client.create_namespaced_job(body=job,
                                                                  namespace=job_namespace)
        except ApiException as e:
            status_code = 503 if e.status == 500 else e.status
            raise ManagerException(str(e), status_code=status_code)
        return job

    def get_job_pods(self, name):
        """
        Returns all the pods created as part of job.
        """
        job_namespace = self.config.get('JOB_NAMESPACE')
        return self.kube_client.list_namespaced_pod(job_namespace,
                                                    label_selector='job-name='+name)

    def get_pod_log(self, name, container_name=None):
        """
        Get a pod log
        """
        job_namespace = self.config.get('JOB_NAMESPACE')
        try:
            if container_name:
                log = self.kube_client.read_namespaced_pod_log(name=name,
                                                               namespace=job_namespace,
                                                               container=container_name)
            else:
                log = self.kube_client.read_namespaced_pod_log(name=name,
                                                               namespace=job_namespace)
        except ApiException:
            log = ''
        return log

    def get_pod_status(self, name):
        """
        Get a pod's status
        """
        job_namespace = self.config.get('JOB_NAMESPACE')
        status = self.kube_client.read_namespaced_pod_status(name=name,
                                                          namespace=job_namespace)
        return status
