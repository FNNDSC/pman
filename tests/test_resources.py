
import logging
from pathlib import Path
import shutil
import os
import time
from unittest import TestCase
from unittest import mock, skip

from flask import url_for

from pman.app import create_app


class ResourceTests(TestCase):
    """
    Base class for all the resource tests.
    """
    def setUp(self):
        # avoid cluttered console output (for instance logging all the http requests)
        logging.disable(logging.WARNING)

        self.app = create_app({
            'TESTING': True,
        })
        self.client = self.app.test_client()

    def tearDown(self):
        # re-enable logging
        logging.disable(logging.NOTSET)


class TestJobList(ResourceTests):
    """
    Test the JobList resource.
    """
    def setUp(self):
        super().setUp()
        with self.app.test_request_context():
            self.url = url_for('api.joblist')

        self.job_id = 'chris-jid-1'

        jobdir_prefix = self.app.config.get('JOBDIR_PREFIX')
        self.share_dir = os.path.join('/home/localuser/storeBase', jobdir_prefix + self.job_id)
        incoming = os.path.join(self.share_dir, 'incoming')
        outgoing = os.path.join(self.share_dir, 'outgoing')
        Path(incoming).mkdir(parents=True, exist_ok=True)
        Path(outgoing).mkdir(parents=True, exist_ok=True)
        with open(os.path.join(incoming, 'test.txt'), 'w') as f:
            f.write('job input test file')

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(self.share_dir)

    def test_get(self):
        response = self.client.get(self.url)
        self.assertTrue('server_version' in response.json)

    def test_post(self):

        data = {
            'jid': self.job_id,
            'cmd_args': '--saveinputmeta --saveoutputmeta --dir /share/incoming',
            'auid': 'cube',
            'number_of_workers': '1',
            'cpu_limit': '1000',
            'memory_limit': '200',
            'gpu_limit': '0',
            'image': 'fnndsc/pl-simplefsapp',
            'selfexec': 'simplefsapp',
            'selfpath': '/usr/local/bin',
            'execshell': '/usr/local/bin/python',
            'type': 'fs',
        }
        # make the POST request
        response = self.client.post(self.url, json=data)
        self.assertIn('status', response.json)

        time.sleep(6)
        with self.app.test_request_context():
            # test get job status and cleanup swarm job
            url = url_for('api.job', job_id=self.job_id)
            response = self.client.get(url)
            self.assertEqual(response.json['status'], 'finishedSuccessfully')
