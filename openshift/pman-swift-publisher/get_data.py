"""
Pulls the data from Swift and places it into the empty directory
SWIFT_KEY enviornment variable to be passed by the template
"""

import os
import zipfile
import time
import fasteners
from io import BytesIO
from swift_handler import SwiftHandler


class SwiftStore():

    swiftConnection = None


    def _getObject(self, key, b_delete):
        """
        Returns an object associated with the specified key in the specified container
        Deletes the object after returning if specified
        """

        try:
            containerName = key
            key = os.path.join('input','data')
            swiftDataObject = self.swiftConnection.get_object(containerName, key)
            if b_delete:
                self.swiftConnection.delete_object(containerName, key)
                self.qrint('Deleted object with key %s' %key)

        except Exception as exp:
            print(exp)

        return swiftDataObject


    def getData(self, **kwargs):
        """
        Gets the data from the Swift storage, zips and/or encodes it and sends it to the client
        """

        for k,v in kwargs.items():
            if k == 'path':
                key = v
            if k == 'in_dir':
                incoming_dir = v
            if k == 'out_dir':
                outgoing_dir = v

        try:
            swiftHandler = SwiftHandler()
            self.swiftConnection = swiftHandler._initiateSwiftConnection()
            dataObject = self._getObject(key, False)
        except Exception as err:
            print(err)
            
        objectInformation= dataObject[0]
        objectValue= dataObject[1]
        fileContent= objectValue

        fileBytes  = BytesIO(fileContent)

        zipfileObj = zipfile.ZipFile(fileBytes, 'r', compression = zipfile.ZIP_DEFLATED)
        # We are extracting to the file to incoming_dir in container
        zipfileObj.extractall(incoming_dir)
        # Create outgoing_dir directory as the plugin container will output data there after processing.
        if not os.path.exists(outgoing_dir):
            os.makedirs(outgoing_dir)

if __name__ == "__main__":
    incoming_dir = os.environ.get("INCOMING_DIR")
    obj = SwiftStore()
    # The init-storage container in all the pods should acquire the lock
    with fasteners.InterProcessLock("/share/.lockfile"):
        # If "/share/.download-failed" exists, exit with an error code immediately
        if os.path.exists("/share/.download-failed"):
            print("Previous pod failed to download the data. Exiting with failure...")
            exit(1)
        # If there is some data in incoming_dir but "/share/.download-succeeded" doesn't exist, it is a failure case
        # Exit with error code immediately
        if os.path.exists(incoming_dir) and len(os.listdir(incoming_dir)) > 0 and not os.path.exists('/share/.download-succeeded'):
            print("Some data was downloaded, but '/share/.download-succeeded' file doen't exist. Exiting with failure...")
            exit(1)
        # Download the data if "/share/.download-succeeded" does not exist
        if not os.path.exists('/share/.download-succeeded'):
            try:
                print("Lock acquired. Downloading data from Swift...")
                obj.getData(path=os.environ.get('SWIFT_KEY'), in_dir=incoming_dir, out_dir=os.environ.get('OUTGOING_DIR'))
            except Exception as err:
                print("Failed to download the data:", err)
                # Create a failed file, if download failed to complete
                os.mknod("/share/.download-failed")
                exit(1)
            # Create a success file, if download completed successfully
            os.mknod("/share/.download-succeeded")
    print("Data downloaded!")
