"""
Takes the output data in the share directory and pushes it into Swift
SWIFT_KEY enviornment variable to be passed by the template
"""

import os
import zipfile
from swift_handler import SwiftHandler


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

    def zipdir(self, path, ziph, **kwargs):
        """
        Zip up a directory.

        :param path:
        :param ziph:
        :param kwargs:
        :return:
        """
        str_arcroot = ""
        for k, v in kwargs.items():
            if k == 'arcroot':  str_arcroot = v
        for root, dirs, files in os.walk(path):
            for file in files:
                str_arcfile = os.path.join(root, file)
                if len(str_arcroot):
                    str_arcname = str_arcroot.split('/')[-1] + str_arcfile.split(str_arcroot)[1]
                else:
                    str_arcname = str_arcfile
                try:
                    ziph.write(str_arcfile, arcname=str_arcname)
                except:
                    print("Skipping %s" % str_arcfile)

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
        fileName = '/share/outgoing'
        # TODO: @ravig. The /tmp should be large enough to hold everything.
        ziphandler = zipfile.ZipFile('/tmp/ziparchive.zip', 'w', zipfile.ZIP_DEFLATED)
        self.zipdir(fileName, ziphandler, arcroot=fileName)

        try:
            with open('/tmp/ziparchive.zip','rb') as f:
                #TODO: @ravig - Change this so that this is scalable.
                zippedFileContent = f.read()
        finally:
            ziphandler.close()
            os.remove('/tmp/ziparchive.zip')

        swiftHandler = SwiftHandler()
        self.swiftConnection = swiftHandler._initiateSwiftConnection()
       
        try:
            containerName = key
            key = os.path.join('output','data') 
            self._putObject(containerName, key, zippedFileContent)
        except Exception as err:
            print(err)
        
        finally:    
            #Delete temporary empty directory created by Swift
            swiftHandler._deleteEmptyDirectory(key)


def put_data_back():
    swiftStore = SwiftStore()
    swiftStore.storeData(path=os.environ.get('SWIFT_KEY'))
