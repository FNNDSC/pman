"""
Pulls the data from Swift and places it into the empty directory
SWIFT_KEY enviornment variable to be passed by the template
"""

import os
import zipfile
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
        # We are extracting to the file to /share/incoming in container as plugin container is hardcoded to read from
        # /share/incoming.
        # TODO: @ravig. Remove this hardcoding. Need to have named arguments in all plugins.
        zipfileObj.extractall('/share/incoming')
        # Create /share/outgoing directory
        if not os.path.exists('/share/outgoing'):
            os.makedirs('/share/outgoing')

        

if __name__ == "__main__":

    obj = SwiftStore()
    obj.getData(path= os.environ.get('SWIFT_KEY'))