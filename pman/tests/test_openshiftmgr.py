import unittest
from unittest.mock import patch, MagicMock
import random
import string
import kubernetes
from pman.openshiftmgr import OpenShiftManager

class OpenShiftManagerTests(unittest.TestCase):
    """
    Test the OpenShiftManager's methods
    """

    @patch('pman.openshiftmgr.config.load_kube_config')
    def setUp(self, mock_config):
        self.project = 'myproject'
        self.manager = OpenShiftManager(self.project)
        self.manager.init_openshift_client()
        self.job_name = 'job' + ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
        self.image = 'fedora'
        self.command = 'echo test'

    @patch('kubernetes.client.apis.batch_v1_api.BatchV1Api.create_namespaced_job')
    def test_schedule(self, mock_create):
        mock_create.return_value = kubernetes.client.models.v1_job.V1Job()
        job = self.manager.schedule(self.image, self.command, self.job_name)
        self.assertIsInstance(job, kubernetes.client.models.v1_job.V1Job)
        #mock_create.assert_called_once() Available in 3.6

    @patch('kubernetes.client.apis.batch_v1_api.BatchV1Api.read_namespaced_job')
    def test_get_job(self, mock_get):
        mock_get.return_value = kubernetes.client.models.v1_job.V1Job()
        job = self.manager.get_job(self.job_name)
        #mock_get.assert_called_once() Available in 3.6
        mock_get.assert_any_call(self.job_name, self.project)
        self.assertIsInstance(job, kubernetes.client.models.v1_job.V1Job)

    @patch('kubernetes.client.apis.batch_v1_api.BatchV1Api.delete_namespaced_job')
    def test_remove(self, mock_delete):
        job = self.manager.remove(self.job_name)
        #mock_delete.assert_called_once() Available in 3.6
        mock_delete.assert_any_call(self.job_name, self.project, {})

if __name__ == '__main__':
    unittest.main()