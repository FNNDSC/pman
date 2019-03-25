import yaml
import json
import os
from kubernetes import client as k_client, config
from kubernetes.client.rest import ApiException
import time, datetime

class Reaper(object):
    def __init__(self,project=None):
        self.kube_client = None
        self.kube_v1_batch_client = None
        self.project = project or os.environ.get('OPENSHIFTMGR_PROJECT') or 'myproject'
        self.kube_v1_delete = None
        self.age = os.environ.get('AGE') or '1'
        self.age = int(self.age)

        # init the kube client
        self.init_kube_client()

    def init_kube_client(self):
        """
        Method to get a kube client connected to remote or local kube api
        """
        kubecfg_path = os.environ.get('KUBECFG_PATH')
        if kubecfg_path is None:
            config.load_kube_config()
        else:
            config.load_kube_config(config_file='/tmp/.kube/config') 
        self.kube_client = k_client.CoreV1Api()
        self.kube_v1_batch_client = k_client.BatchV1Api()
        self.kube_v1_delete = k_client.V1DeleteOptions()

    def get_jobs(self, age=1):
        """
        Get all previously scheduled jobs for the namespace that are older than specified age, default is 1, for reaper to terminate
        age : <int> Time elapsed from start of job in days
        """
        jobs_for_reaper = []
        try: 
            api_response = self.kube_v1_batch_client.list_namespaced_job(namespace=self.project, label_selector='job-origin=pman', include_uninitialized=True)
            for item in api_response.items:
                # Checking if job has finished running, either failed or succeeded
                if item.status.conditions and (item.status.failed or item.status.succeeded):
                    # Using start_time because failed jobs have no completion_time
                    start_time = item.status.start_time
                    current_time = datetime.datetime.now(datetime.timezone.utc)
                    diff = current_time-start_time
                    # 86400 = number of seconds in a day. "divmod" returns quotient and remainder as tuple e.g (1, 5.74943)
                    # means 1 day and 5.74943 sec have passed between current_time and start_time of the job
                    diff_in_seconds = divmod(diff.total_seconds(), 86400)
                    if diff_in_seconds[0] >= 1:
                        jobs_for_reaper.append(item.metadata.name)
               
        except ApiException as e:
            print("Exception when calling BatchV1Api->list_namespaced_job: %s\n" % e)
            exit(1)
        return jobs_for_reaper

    def delete_jobs(self):
        """
        Deletes jobs in the namespace older than age specified
        jobs : <List> list of jobs to be deleted
        """
        jobs = self.get_jobs(self.age)
        print('Jobs queued for delete: ', jobs)
        for job in jobs:
            try: 
                body = k_client.V1DeleteOptions(propagation_policy='Background')
                self.kube_v1_batch_client.delete_namespaced_job(job, body=body, namespace=self.project)
                self.kube_client.delete_namespaced_persistent_volume_claim(job+"-storage-claim", self.project, {})
                print('Deleted job: ', job)
            except ApiException as e:
                print("Exception when calling BatchV1Api -> delete_namespaced_job: %s\n" % e)
                exit(1)

if __name__ == '__main__':
    reaper = Reaper()
    reaper.delete_jobs()
    exit(0)