"""
Helper class for get_data and put_data
Establishes swift connection and returns a connection object
"""

import os
import configparser
from keystoneauth1.identity import v3
from keystoneauth1 import session
from swiftclient import client as swift_client

class SwiftHandler():

    def _getScopedSession(self, osAuthUrl, username, password, osProjectDomain, osProjectName):
        """
        Uses keystone authentication to create and return a scoped session
        """

        passwordAuth = v3.Password(auth_url=osAuthUrl,
                            user_domain_name='default',
                            username=username, password=password,
                            project_domain_name=osProjectDomain,
                            project_name=osProjectName,
                            unscoped=False)

        scopedSession = session.Session(auth= passwordAuth)
        return scopedSession


    def _initiateSwiftConnection(self, **kwargs):
        """
        Initiates a Swift connection and returns a Swift connection object
        Swift credentials should be stored as a cfg file at /etc 
        """
        
        for k,v in kwargs:
            if k == 'configPath': configPath= v

        configPath = '/etc/swift/swift-credentials.cfg'

        config = configparser.ConfigParser()
        try:
            f = open(configPath, 'r')
            config.readfp(f)
        finally:
            f.close()
        
        osAuthUrl              = config['AUTHORIZATION']['osAuthUrl']
        username               = config['AUTHORIZATION']['username']
        password               = config['AUTHORIZATION']['password']
        osProjectDomain        = config['PROJECT']['osProjectDomain']
        osProjectName          = config['PROJECT']['osProjectName']
        
        scopedSession = self._getScopedSession(osAuthUrl, username, password, osProjectDomain, osProjectName)
        swiftConnection = swift_client.Connection(session=scopedSession)
        return swiftConnection


    def _deleteEmptyDirectory(self, key):
        """
        Deletes the empty directory created by Swift in the parent directory
        """

        directoryPath = os.path.join(os.path.dirname(__file__), '../%s'%key)
        try:
            os.rmdir(directoryPath)
            print("Temporary directory %s deleted"%key)
        except:
            print("No temporary directory found")
