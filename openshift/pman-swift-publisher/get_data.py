"""
Pulls the data from Swift and places it into the empty directory
SWIFT_KEY enviornment variable to be passed by the template
"""

import os
import zipfile
import configparser
from keystoneauth1.identity import v3
from keystoneauth1 import session
from swiftclient import client as swift_client
from io import BytesIO
from swift_handler import swiftHandler


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
            if k== 'path': key= v

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
        zipfileObj.extractall('/share')
        

if __name__ == "__main__":

    obj = SwiftStore()
    obj.getData(path= os.environ.get('SWIFT_KEY'))