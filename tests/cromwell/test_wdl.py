import unittest
from pman.e2_wdl import ChRISJob
from pman.cromwell.models import WorkflowMetadataResponse
import tests.cromwell.examples.metadata as examples
from serde.json import from_json


class WdlTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.example1: WorkflowMetadataResponse = from_json(WorkflowMetadataResponse, examples.response_notstarted)
        cls.example2: WorkflowMetadataResponse = from_json(WorkflowMetadataResponse, examples.response_queued)

    def test_parse_wdl(self):
        self.assertEqual(examples.expected_notstarted, ChRISJob.from_wdl(self.example1.submittedFiles.workflow))
        self.assertEqual(examples.expected_queued, ChRISJob.from_wdl(self.example2.submittedFiles.workflow))


if __name__ == '__main__':
    unittest.main()
