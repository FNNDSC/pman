
import logging
import unittest
from pathlib import Path
import shutil
import os
import time
from unittest import TestCase

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


@unittest.skipIf('STOREBASE' not in os.environ,
                 'Cannot start pman without STOREBASE')
class TestJobListResource(ResourceTests):
    """
    Test the JobListResource resource.
    """
    def setUp(self):
        super().setUp()
        with self.app.test_request_context():
            self.url = url_for('api.joblist')

        self.job_id = 'chris-jid-1'

        self.share_dir = os.path.join('/var/local/storeBase', 'key-' + self.job_id)
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
        self.assertEqual(response.status_code, 200)
        self.assertTrue('server_version' in response.json)

    def test_post(self):

        data = {
            'jid': self.job_id,
            'args': ['--saveinputmeta', '--saveoutputmeta', '--dir', '/share/incoming'],
            'auid': 'cube',
            'number_of_workers': '1',
            'cpu_limit': '1000',
            'memory_limit': '200',
            'gpu_limit': '0',
            'image': 'fnndsc/pl-simplefsapp',
            'entrypoint': ['simplefsapp'],
            'type': 'fs',
        }
        # make the POST request
        response = self.client.post(self.url, json=data)
       
        self.assertEqual(response.status_code, 201)
        self.assertIn('status', response.json)

        time.sleep(5)
        with self.app.test_request_context():
            # test get job status
            url = url_for('api.job', job_id=self.job_id)
            response = self.client.get(url)
            if response.json['status'] != 'finishedSuccessfully':
                time.sleep(10)
                response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['status'], 'finishedSuccessfully')

            # test remove job (cleanup swarm job)
            response = self.client.delete(url)
            self.assertEqual(response.status_code, 204)
