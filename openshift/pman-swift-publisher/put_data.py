"""
Takes the output data in the share directory and pushes it into Swift
SWIFT_KEY environment variable to be passed by the template
"""

import os
import shutil
from swift_handler import SwiftHandler
import fasteners
from kubernetes import client, config, watch
import time
from lockfile import LockFile


class SwiftStore():
    swiftConnection = None

    def _putObject(self, containerName, key, value):
        """
        Creates an object with the given key and value and puts the object in the specified container
        """

        try:
            self.swiftConnection.put_object(containerName, key , contents=value, content_type='text/plain')
            print('Object added with key %s' %key)

        except Exception as exp:
            print('Exception = %s' %exp)

    def storeData(self, **kwargs):
        """
        Creates an object of the file and stores it into the container as key-value object 
        """

        key = ''
        for k, v in kwargs.items():
            if k == 'path':
                key = v
        # The plugin container is hardcoded to output data to /share/outgoing after processing.
        # TODO:@ravig. Remove this hardcoding.

        lockfile = '/share/putdatalockfile1'
        lock = LockFile(lockfile)
        am_i_worker=False
        with lock:
            try:
                if  not lock.is_locked():
                    lock.acquire()
                    time.sleep(2)
                    print ('Master acquired lock')
                    if self.watch():
                        try:
                            shutil.make_archive('/tmp/ziparchive', 'zip', '/share/outgoing')
                            with open('/tmp/ziparchive.zip', 'rb') as f:
                                zippedFileContent = f.read()
                        except Exception as err:
                            print('Some error so releasing lock')
                            print(err)
                            lock.release()
                            shutil.rmtree('/share/outgoing', ignore_errors=True)
                        finally:
                            os.remove('/tmp/ziparchive.zip')

                        swiftHandler = SwiftHandler()
                        self.swiftConnection = swiftHandler._initiateSwiftConnection()

                        containerName = key
                        key = os.path.join('output', 'data')
                        self._putObject(containerName, key, zippedFileContent)
                        swiftHandler._deleteEmptyDirectory(key)

                    
                else:
                    print ("I am side kick. I should exit quitely.")
                    am_i_worker=True
                    exit()
                

            except Exception as err:
                print (err)
                print("Lock acquiring failed meaning some other process is still using the lock file (or) file download failed. Wait for sometime and eventually exit after n hours/min")
            finally:
                if not am_i_worker and lock.is_locked():
                    print ("Inside put_data doing clean up")
                    lock.release()
                    shutil.rmtree('/share/outgoing', ignore_errors=True)
                    shutil.rmtree('/share/putdatalockfile1', ignore_errors=True)
    
    #There is a need to write generic watch function for both put_data.py and watch.py
    #https://stackoverflow.com/questions/35405968/how-could-i-pass-block-to-a-function-in-python-which-is-like-the-way-to-pass-blo
    def watch(self):
        kubecfg_path = os.environ.get('KUBECFG_PATH')
        if kubecfg_path is None:
            config.load_kube_config()
        else:
            config.load_kube_config(config_file=kubecfg_path)
        v1_client = client.CoreV1Api()
        resrc_version = None
        namespace = os.getenv("OPENSHIFTMGR_PROJECT", "myproject")
        job_id = os.getenv("SWIFT_KEY")
        
        
        w = watch.Watch()
        if resrc_version is None:
            stream = w.stream(v1_client.list_namespaced_pod, namespace,label_selector='job-name='+job_id)
        else:
            stream = w.stream(v1_client.list_namespaced_pod, namespace, resource_version=resrc_version,label_selector='job-name='+job_id)
       
        #total_workers: Total number of worker requested for the job
        total_workers=int(os.getenv("NUMBER_OF_WORKERS",1))
        #completed_workers: Count to check number of workers in "Completed" state.
        completed_workers=1
        
       #Keep reading events untill all but one worker has completed
        while True:
            for event in stream:
                resrc_version = event['raw_object']['metadata']['resourceVersion']
                if 'containerStatuses' in event['raw_object']['status']:
                    for status in event['raw_object']['status']['containerStatuses']:
                        if status['name'] == 'publish' and 'terminated' in status['state'] and status['state']['terminated']['reason'] == 'Completed':
                            completed_workers+=1
                            print (completed_workers)
                            # If all but one worker is in "Completed" state, quit watch and upload to Swift
                            if total_workers==completed_workers:
                                w.stop()
                                return True
                                




def put_data_back():
    swiftStore = SwiftStore()
    swiftStore.storeData(path=os.environ.get('SWIFT_KEY'))
