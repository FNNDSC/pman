"""
OpenShift cluster manager module that provides functionality to schedule jobs as well as
manage their state in the cluster.
"""

import yaml
import json
import os
from kubernetes import client as k_client
from openshift import client as o_client
from openshift import config


class OpenShiftManager(object):

    def __init__(self, project=None):
        self.openshift_client = None
        self.kube_client = None
        self.kube_v1_batch_client = None
        self.project = project or os.environ.get('OPENSHIFTMGR_PROJECT') or 'myproject'

        # init the openshift client
        self.init_openshift_client()

    def init_openshift_client(self):
        """
        Method to get a OpenShift client connected to remote or local OpenShift
        """
        kubecfg_path = os.environ.get('KUBECFG_PATH')
        if kubecfg_path is None:
            config.load_kube_config()
        else:
            config.load_kube_config(config_file=kubecfg_path)
        self.openshift_client = o_client.OapiApi()
        self.kube_client = k_client.CoreV1Api()
        self.kube_v1_batch_client = k_client.BatchV1Api()

    def schedule(self, image, command, name):
        """
        Schedule a new job and returns the job object.
        """
        job_str = """
apiVersion: batch/v1
kind: Job
metadata:
  name: {name}
spec:
    parallelism: 1
    completions: 1
    activeDeadlineSeconds: 3600
    template:
        metadata:
          name: {name}
        spec:
            restartPolicy: Never
            initContainers:
            - name: init-storage
              image: adi95docker/pman-swift-publisher
              env:
              - name: SWIFT_KEY
                value: {name}
              command: ['python3', 'get_data.py']
              volumeMounts:
              - mountPath: /share
                name: shared-volume
              - mountPath: /etc/swift
                name: swift-credentials
                readOnly: true
            containers:
            - name: {name}
              image: {image}
              command: {command}
              volumeMounts:
              - mountPath: /share
                name: shared-volume
            - name: publish
              image: adi95docker/pman-swift-publisher
              env:
              - name: SWIFT_KEY
                value: {name}
              command: ['sh', 'check-status.sh']
              volumeMounts:
              - mountPath: /share
                name: shared-volume
              - mountPath: /etc/swift
                name: swift-credentials
                readOnly: true
""".format(name=name, command=str(command.split(" ")), image=image)
        job_str += """
            volumes:
            - name: shared-volume
              emptyDir: {}
            - name: swift-credentials
              secret: 
                secretName: swift-credentials
"""

        job_yaml = yaml.load(job_str)
        job = self.kube_v1_batch_client.create_namespaced_job(namespace=self.project, body=job_yaml)
        return job

    def create_pod(self, image, name):
        """
        Create a pod
        """
        pod_str = """
apiVersion: v1
kind: Pod
metadata:
    name: {name}
spec:
    restartPolicy: Never
    containers:
    - name: {name}
      image: {image}
""".format(name=name, image=image)

        pod_yaml = yaml.load(pod_str)
        pod = self.kube_client.create_namespaced_pod(namespace=self.project, body=pod_yaml)
        return pod

    def get_pod_status(self, name):
        """
        Get a pod's status
        """
        log = self.kube_client.read_namespaced_pod_status(namespace=self.project, name=name)
        return log

    def get_pod_log(self, name):
        """
        Get a pod log
        """
        log = self.kube_client.read_namespaced_pod_log(namespace=self.project, name=name)
        return log

    def get_job(self, name):
        """
        Get the previously scheduled job object
        """
        return self.kube_v1_batch_client.read_namespaced_job(name, self.project)

    def remove(self, name):
        """
        Remove a previously scheduled job
        """
        self.kube_v1_batch_client.delete_namespaced_job(name, self.project, {})

    def state(self, name):
        """
        Return the state of a previously scheduled job
        """
        job = self.get_job(name)
        message = None
        state = None
        reason = None
        if job.status.conditions:
            for condition in job.status.conditions:
                if condition.type == 'Failed' and condition.status == 'True':
                    message = 'started'
                    reason = condition.reason
                    state = 'failed'
                    break
        if not state:
            if job.status.completion_time and job.status.succeeded > 0:
                message = 'finished'
                state = 'complete'
            elif job.status.active > 0:
                message = 'started'
                state = 'running'
            else:
                message = 'inactive'
                state = 'inactive'

        return {'Status': {'Message': message,
                                'State': state,
                                'Reason': reason,
                                'Active': job.status.active,
                                'Failed': job.status.failed,
                                'Succeeded': job.status.succeeded,
                                'StartTime': job.status.start_time,
                                'CompletionTime': job.status.completion_time}}