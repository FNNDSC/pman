"""
Kubernetes cluster manager module that provides functionality to schedule jobs as well
as manage their state in the cluster.
"""
import json
from typing import AnyStr, Optional
import logging

from kubernetes import client as k_client
from kubernetes import config as k_config
from kubernetes.client import V1Pod
from kubernetes.client.models.v1_job import V1Job
from kubernetes.client.rest import ApiException
from .abstractmgr import (AbstractManager, ManagerException, JobInfo, JobStatus,
                          TimeStamp, JobName)

logger = logging.getLogger(__name__)


class KubernetesManager(AbstractManager[V1Job]):

    def __init__(self, config_dict=None):
        super().__init__(config_dict)

        k_config.load_incluster_config()
        self.kube_client = k_client.CoreV1Api()
        self.kube_v1_batch_client = k_client.BatchV1Api()

    def schedule_job(self, image, command, name, resources_dict, env, uid, gid,
                     mounts_dict) -> V1Job:
        """
        Schedule a new job and return the job object.
        """
        job_instance = self.create_job(image, command, name, resources_dict, env, uid,
                                       gid, mounts_dict)
        job = self.submit_job(job_instance)
        return job

    def get_job(self, name) -> V1Job:
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

    def get_job_logs(self, job: V1Job, tail: int) -> AnyStr:
        # TODO: Think of a better way to abstract out logs in case of multiple pods running parallelly

        logs = ''
        pods = self.get_job_pods(job.metadata.name)
        for pod_item in pods.items:
            pod_name = pod_item.metadata.name
            logs += self.get_pod_log(pod_name, tail)

            # Bad: if job dies to OOMKilled, add the reason of death to the logs,
            # and return immediately.
            term_reason = self.__get_termination_reason(pod_item)
            if term_reason is not None:
                if term_reason != 'Completed':
                    logs += f'\n{term_reason}'
                return logs
        return logs

    @staticmethod
    def __get_termination_reason(pod: V1Pod) -> Optional[str]:
        if not pod.status.container_statuses:
            return None
        termination = pod.status.container_statuses[0].state.terminated
        if termination is None:
            return None
        return termination.reason

    def get_job_info(self, job) -> JobInfo:
        """
        Get the job's info dictionary for a previously scheduled job object.
        """
        status = JobStatus.notstarted
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
                        status = JobStatus.finishedWithError
                        break
        if status == JobStatus.notstarted:
            if completion_time and succeeded:
                message = 'finished'
                status = JobStatus.finishedSuccessfully
            elif job.status.active:
                message = 'running'
                status = JobStatus.started
            else:
                if job.status.active is None and failed is None and succeeded is None:
                    # job status is being polled while pod is finishing up, or idk. just a strange bug.
                    # https://github.com/FNNDSC/pman/issues/225
                    logger.warning(f'job status is all None: {job.to_dict()}')
                    message = 'job is finishing, job.status is None'
                    status = JobStatus.started
                else:
                    message = 'inactive'
                    status = JobStatus.undefined
                    logger.warning(f'cannot figure out info: job={job.to_dict()}, status={job.status.to_dict()}')

        return JobInfo(
            name=JobName(job.metadata.name),
            image=job.spec.template.spec.containers[0].image,
            cmd=' '.join(job.spec.template.spec.containers[0].command),
            timestamp=TimeStamp(completion_time.isoformat() if completion_time is not None else ''),
            message=message,
            status=status
        )

    def remove_job(self, job):
        """
        Remove a previously scheduled job.
        """
        job_namespace = self.config.get('JOB_NAMESPACE')
        body = k_client.V1DeleteOptions(propagation_policy='Background')
        self.kube_v1_batch_client.delete_namespaced_job(job.metadata.name, body=body,
                                                        namespace=job_namespace)

    def create_job(self, image, command, name, resources_dict, env_l, uid, gid,
                   mounts_dict) -> V1Job:
        """
        Create and return a new job instance.
        """
        number_of_workers = resources_dict.get('number_of_workers')
        cpu_limit = str(resources_dict.get('cpu_limit')) + 'm'
        memory_limit = str(resources_dict.get('memory_limit')) + 'Mi'
        gpu_limit = resources_dict.get('gpu_limit')

        # About requests and limits:
        # https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
        #
        # > Note: If a container specifies its own memory limit, but does not specify a memory
        # > request, Kubernetes automatically assigns a memory request that matches the limit.

        limits = {'memory': memory_limit, 'cpu': cpu_limit}

        env = []
        for s in env_l:
            key, val = s.split('=', 1)
            env.append(k_client.V1EnvVar(name=key, value=val))

        if gpu_limit > 0:
            # ref: https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/
            limits['nvidia.com/gpu'] = gpu_limit
            env.append(k_client.V1EnvVar(name='NVIDIA_VISIBLE_DEVICES', value='all'))
            env.append(k_client.V1EnvVar(name='NVIDIA_DRIVER_CAPABILITIES',
                                         value='compute,utility'))
            env.append(k_client.V1EnvVar(name='NVIDIA_REQUIRE_CUDA', value='cuda>=9.0'))

        security_context = {
            'allow_privilege_escalation': False,
            'capabilities': k_client.V1Capabilities(drop=['ALL'])
        }

        if uid is not None:
            security_context['run_as_user'] = uid
        if gid is not None:
            security_context['run_as_group'] = gid

        pvc = k_client.V1PersistentVolumeClaimVolumeSource(
            claim_name=self.config.get('VOLUME_NAME')
        )
        volume = k_client.V1Volume(
            name='storebase',
            persistent_volume_claim=pvc,

        )
        volume_mount_inputdir = k_client.V1VolumeMount(
            mount_path=mounts_dict['inputdir_target'],
            name='storebase',
            sub_path=mounts_dict['inputdir_source'],
            read_only=True
        )
        volume_mount_outputdir = k_client.V1VolumeMount(
            mount_path=mounts_dict['outputdir_target'],
            name='storebase',
            sub_path=mounts_dict['outputdir_source'],
            read_only=False
        )

        dshm_volume = []
        dshm_mount = []
        if (s := self.config.get('SHM_SIZE')) is not None:
            dshm_volume.append(k_client.V1Volume(
                name='dshm',
                empty_dir=k_client.V1EmptyDirVolumeSource(
                    medium='Memory',
                    size_limit=s.as_mib()
                )
            ))
            dshm_mount.append(k_client.V1VolumeMount(
                mount_path='/dev/shm',
                name='dshm',
            ))

        container = k_client.V1Container(
            name=name,
            image=image,
            env=env,
            command=command,
            security_context=k_client.V1SecurityContext(**security_context),
            resources=k_client.V1ResourceRequirements(limits=limits),
            volume_mounts=[volume_mount_inputdir, volume_mount_outputdir, *dshm_mount]
        )

        pod_template_metadata = None
        labels_config = self.config.get('JOB_LABELS')
        if labels_config:
            pod_template_metadata = k_client.V1ObjectMeta(labels=labels_config)

        node_selector = self.config.get('NODE_SELECTOR')

        pod_spec_args = {
            'restart_policy': 'Never',
            'containers': [container],
            'volumes': [volume, *dshm_volume],
        }

        if node_selector:
            pod_spec_args['node_selector'] = node_selector

        image_pull_secrets = self.config.get('IMAGE_PULL_SECRETS')
        if image_pull_secrets:
            pod_spec_args['image_pull_secrets'] = image_pull_secrets

        template = k_client.V1PodTemplateSpec(
            metadata=pod_template_metadata,
            spec=k_client.V1PodSpec(**pod_spec_args),
        )
        # configure job's spec
        spec = k_client.V1JobSpec(
            parallelism=number_of_workers,
            completions=number_of_workers,
            backoff_limit=0,
            ttl_seconds_after_finished=86400,  # 24h
            active_deadline_seconds=604800,    # 1 week
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

    def get_pod_log(self, pod_name: str, tail: int) -> AnyStr:
        job_namespace = self.config.get('JOB_NAMESPACE')
        try:
            log = self.kube_client.read_namespaced_pod_log(
                name=pod_name,
                namespace=job_namespace,
                tail_lines=tail
            )
        except ApiException as e:
            if self.__is_container_creating_error(e):
                log = json.loads(e.body)['message']
            else:
                log = 'Error: check pman logs.'
                logger.error('Exception getting logs for pod="%s": %s', pod_name, str(e))
        return log

    @staticmethod
    def __is_container_creating_error(e: ApiException) -> bool:
        return (
            e.body is not None
            and 'message' in str(e.body)
            and 'ContainerCreating' in str(e.body)
        )

    def get_pod_status(self, name):
        """
        Get a pod's status
        """
        job_namespace = self.config.get('JOB_NAMESPACE')
        status = self.kube_client.read_namespaced_pod_status(name=name,
                                                          namespace=job_namespace)
        return status
