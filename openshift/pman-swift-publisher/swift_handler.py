"""
Helper class for get_data and put_data
Establishes swift connection and returns a connection object
"""

import os
import configparser
from keystoneauth1.identity import v3
from keystoneauth1 import session
from swiftclient import service as swift_service

def _createSwiftService(configPath):
    config = configparser.ConfigParser()
    try:
        f = open(configPath, 'r')
        config.readfp(f)
    finally:
        f.close()

    options = {
        'auth_version':         3,
        'os_auth_url':          config['AUTHORIZATION']['osAuthUrl'],
        'os_username':          config['AUTHORIZATION']['username'],
        'os_password':          config['AUTHORIZATION']['password'],
        'os_project_domain_name':    config['PROJECT']['osProjectDomain'],
        'os_project_name':      config['PROJECT']['osProjectName']
    }

    service = swift_service.SwiftService(options)
    return service

def _deleteEmptyDirectory(key):
    """
    Deletes the empty directory created by Swift in the parent directory
    """

    directoryPath = os.path.join(os.path.dirname(__file__), '../%s'%key)
    try:
        os.rmdir(directoryPath)
        print("Temporary directory %s deleted"%key)
    except:
        print("No temporary directory found")
