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
        'os_auth_url': config['AUTHORIZATION']['osAuthUrl'],
        'application_id': config['SECRET']['applicationId'],
        'application_secret': config['SECRET']['applicationSecret'],
    }

    auth_swift = v3.application_credential.ApplicationCredential(
        options['os_auth_url'],
        application_credential_id=options['application_id'],
        application_credential_secret=options['application_secret']
    )

    session_client = session.Session(auth=auth_swift)
    service = swift_service.Connection(session=session_client)
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
