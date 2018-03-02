"Watch the image processing container, once it is done move the data back to swift storage"

from kubernetes import client, config, watch
from put_data import put_data_back
import os

# Keep track of PR https://github.com/kubernetes-client/python-base/pull/36
# it is implementing watching forever and reconnecting if the connection is lost
# If the PR doesn't get in soon enough, need to figure out how to do that here

def main():
    kubecfg_path = os.environ.get('KUBECFG_PATH')
    if kubecfg_path is None:
        config.load_kube_config()
    else:
        config.load_kube_config(config_file=kubecfg_path)
    v1_client = client.CoreV1Api()
    resrc_version = None
    namespace = os.getenv("OPENSHIFTMGR_PROJECT", "myproject")
    w = watch.Watch()

    while True:
        if resrc_version is None:
            stream = w.stream(v1_client.list_namespaced_pod, namespace)
        else:
            stream = w.stream(v1_client.list_namespaced_pod, namespace, resource_version=resrc_version)
        for event in stream:
            resrc_version = event['raw_object']['metadata']['resourceVersion']
            if 'containerStatuses' in event['raw_object']['status']:
                for status in event['raw_object']['status']['containerStatuses']:
                    if status['name'] != 'publish' and 'terminated' in status['state']:
                        w.stop()
                        # It is possible for the image processing container to error out
                        # when that happens, the reason will be "Error" and this will return false
                        return status['state']['terminated']['reason'] == 'Completed'

if __name__ == '__main__':
    if main():
        put_data_back()
    else:
        print("Image processing container failed to complete")

