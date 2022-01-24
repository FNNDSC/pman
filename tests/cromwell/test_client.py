import unittest
from unittest.mock import Mock
from tests.cromwell.helpers import patch_cromwell_api
from cromwell_tools.cromwell_auth import CromwellAuth
from pman.cromwell.client import CromwellClient
from pman.cromwell.models import WorkflowId, WorkflowStatus
import tests.cromwell.examples.metadata as metadata_example


class CromwellClientTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = CromwellClient(CromwellAuth('https://example.com'))

    @patch_cromwell_api('metadata', metadata_example.response_failed)
    def test_metadata_failed(self, _):
        res = self.client.metadata(WorkflowId('wont-work'))
        self.assertEqual(WorkflowStatus.Failed, res.status)
        self.assertEqual(metadata_example.expected_failed.timestamp, res.end)

    @patch_cromwell_api('metadata', metadata_example.response_done)
    def test_metadata_done(self, _):
        res = self.client.metadata(WorkflowId('done-and-dusted'))
        self.assertEqual(WorkflowStatus.Succeeded, res.status)


if __name__ == '__main__':
    unittest.main()
