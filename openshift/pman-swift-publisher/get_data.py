"""
Pulls the data from Swift and places it into the empty directory
SWIFT_KEY environment variable to be passed by the template
"""

import os
import zipfile
import time
import fasteners
import pprint
from io import BytesIO
import swift_handler

pp = pprint.PrettyPrinter(indent=4)


def getData(**kwargs):
    """
    Gets the data from the Swift storage, zips and/or encodes it and sends it to the client
    """

    b_delete = False
    configPath = "/etc/swift/swift-credentials.cfg"

    for k,v in kwargs.items():
        if k == 'containerName':
            containerName = v
        if k == 'in_dir':
            incoming_dir = v
        if k == 'out_dir':
            outgoing_dir = v
        if k == 'delete':
            b_delete = v
        if k == 'config_path':
            configPath = v

    swiftService = swift_handler._createSwiftService(configPath)

    key = "input/data"
    success = True

    if not os.path.exists('/local'):
        os.mkdir('/local')
    downloadResultsGenerator = swiftService.download(containerName, [key], {'out_file': '/local/incomingData.zip'})
    for res in downloadResultsGenerator:
        print("Download results generated")
        if not res['success']:
            success = False
        pp.pprint(res)
    if success:
        print("Download successful")
        if b_delete:
            for res in swiftService.delete(containerName, [key]):
                print("Delete results generated")
                if not res['success']:
                    success = False
                pp.pprint(res)
            if success:
                print('Deleted object with key %s' %key)
        else:
            print("Deletion unsuccessful")
    else:
        print("Download unsuccessful")

    
    zipfileObj = zipfile.ZipFile('/local/incomingData.zip', 'r', compression = zipfile.ZIP_DEFLATED)
    # We are extracting to the file to incoming_dir in container
    zipfileObj.extractall(incoming_dir)
    # Create outgoing_dir directory as the plugin container will output data there after processing.
    if not os.path.exists(outgoing_dir):
        os.makedirs(outgoing_dir)

if __name__ == "__main__":
    incoming_dir = os.environ.get("INCOMING_DIR")
    # The init-storage container in all the pods should acquire the lock
    with fasteners.InterProcessLock("/share/.lockfile"):
        # If "/share/.download-failed" exists, exit with an error code immediately
        if os.path.exists("/share/.download-failed"):
            print("Previous pod failed to download the data. Exiting with failure...")
            exit(1)
        # If there is some data in incoming_dir but "/share/.download-succeeded" doesn't exist, it is a failure case
        # Exit with error code immediately
        if os.path.exists(incoming_dir) and len(os.listdir(incoming_dir)) > 0 and not os.path.exists('/share/.download-succeeded'):
            print("Some data was downloaded, but '/share/.download-succeeded' file doesn't exist. Exiting with failure...")
            exit(1)
        # Download the data if "/share/.download-succeeded" does not exist
        if not os.path.exists('/share/.download-succeeded'):
            try:
                print("Lock acquired. Downloading data from Swift...")
                getData(containerName=os.environ.get('SWIFT_KEY'), in_dir=incoming_dir, out_dir=os.environ.get('OUTGOING_DIR'))
                os.mknod('/local/.download-pod')
            except Exception as err:
                print("Failed to download the data:", err)
                # Create a failed file, if download failed to complete
                os.mknod("/share/.download-failed")
                exit(1)
            # Create a success file, if download completed successfully
            os.mknod("/share/.download-succeeded")
    print("Data downloaded!")
