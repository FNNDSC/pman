"""
Takes the output data in the share directory and pushes it into Swift
SWIFT_KEY environment variable to be passed by the template
"""

import os
import shutil
import pprint
import swift_handler
from kubernetes import client, config, watch
from swiftclient import service as swift_service

pp = pprint.PrettyPrinter(indent=4)

def storeData(**kwargs):
    """
    Creates an object of the file and stores it into the container as key-value object 
    """

    configPath = "/etc/swift/swift-credentials.cfg"
    
    for k, v in kwargs.items():
        if k == 'containerName':
            containerName = v
        if k == 'out_dir':
            outgoing_dir = v
        if k == 'configPath':
            configPath = v

    swiftService = swift_handler._createSwiftService(configPath)

    shutil.make_archive('/local/outgoingData', 'zip', outgoing_dir)
    try:
        success = True
        uploadObject = swift_service.SwiftUploadObject('/local/outgoingData.zip', "output/data")
        uploadResultsGenerator = swiftService.upload(containerName, [uploadObject])
        for res in uploadResultsGenerator:
            print("Upload results generated")
            if not res["success"]:
                success = False
            pp.pprint(res)
    except Exception as err:
        print(err)
        success = False
    if success:
        print("Upload successful")
    else:
        print("Upload unsuccessful")
    #Delete temporary empty directory created by Swift
    swift_handler._deleteEmptyDirectory(containerName)
    os.remove('/local/outgoingData.zip')

class KubeClient():
    def __init__(self):
        self.kubecfg_path = os.environ.get('KUBECFG_PATH')
        if self.kubecfg_path is None:
            config.load_kube_config()
        else:
            config.load_kube_config(config_file='/tmp/.kube/config')
        self.kube_client = client.CoreV1Api()
        self.kube_v1_batch_client = client.BatchV1Api()
        self.kube_v1_delete = client.V1DeleteOptions()
        self.namespace = os.getenv("OPENSHIFTMGR_PROJECT", "myproject")
        self.job_id = os.getenv("SWIFT_KEY")

    def check_before_upload(self):
        """
        Checks for the pod that downloaded objects from Swift for uploading results to Swift.
        Other pods should exit. 
        """
        if os.path.exists('/local/.download-pod'):
            print('I am last pod. Uploading to Swift.')
            return self.watch_containers()
        return False

    def terminate_job(self):
        """
        Partially update the specified Job. Change activeDeadlineSeconds to 0 so that failed job isn't run again.
        """
        body = self.kube_v1_batch_client.read_namespaced_job(self.job_id, self.namespace)
        body.spec.active_deadline_seconds = 0
        api_response=self.kube_v1_batch_client.patch_namespaced_job(self.job_id, self.namespace, body)
        print('Job patched to terminate instantly.')
    
    def watch_containers(self):
        resrc_version = None
        requested_image_plugins = int(os.getenv("NUMBER_OF_WORKERS"))
        w = watch.Watch()

        # Wait until all image processing containers are done.
        while True:
            if resrc_version is None:
                # List all pods for given job using the label_selector to only watch the pods created by the job, 
                # which is defined by job_id
                stream = w.stream(self.kube_client.list_namespaced_pod, self.namespace, label_selector='job-name='+self.job_id)
            else:
                stream = w.stream(self.kube_client.list_namespaced_pod, self.namespace, resource_version=resrc_version, label_selector='job-name='+job_id)
            
            completed_image_plugins = 0
            for event in stream:
                resrc_version = event['raw_object']['metadata']['resourceVersion']
                if 'containerStatuses' in event['raw_object']['status']:
                    for status in event['raw_object']['status']['containerStatuses']:
                        if status['name'] == self.job_id and 'terminated' in status['state']:
                            if status['state']['terminated']['reason'] == 'Error':
                                w.stop()
                                # It is possible for the image processing container to error out when that happens, kill the job and exit.
                                print('Some pod failed so terminate job')
                                # Patch job to terminate. No re run required.
                                self.terminate_job()
                                exit(1)
                            elif status['state']['terminated']['reason'] == 'Completed':
                                completed_image_plugins += 1
                                if completed_image_plugins == requested_image_plugins:
                                    print('All image processing containers are done!')
                                    w.stop()
                                    return True

    def put_data_back(self):
        # Pod that downloaded should upload objects to swift.
        if self.check_before_upload():
            storeData(containerName=os.environ.get('SWIFT_KEY'), out_dir=os.environ.get('OUTGOING_DIR'))
            shutil.rmtree('/share/outgoing', ignore_errors=True)
            shutil.rmtree('/share/outgoing/lockfile', ignore_errors=True)
        else:
            print('I am not last. Exiting.')
            exit(0)

if __name__ == '__main__':
    kubeClient = KubeClient()
    kubeClient.put_data_back()
