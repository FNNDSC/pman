import unittest
from pman.slurmwdl import SlurmJob
from pman.cromwell.models import WorkflowMetadataResponse
import tests.cromwell.examples.metadata as mexamples
import tests.cromwell.examples.wdl as wexamples
from serde.json import from_json


class WdlTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.example1: WorkflowMetadataResponse = from_json(WorkflowMetadataResponse, mexamples.response_notstarted)
        cls.example2: WorkflowMetadataResponse = from_json(WorkflowMetadataResponse, mexamples.response_queued)

    def test_parse_wdl(self):
        self.assertEqual(mexamples.expected_notstarted, SlurmJob.from_wdl(self.example1.submittedFiles.workflow))
        self.assertEqual(mexamples.expected_queued, SlurmJob.from_wdl(self.example2.submittedFiles.workflow))

    def test_get_between_helper(self):
        self.assertEqual(
            (' three ', 14),
            SlurmJob._get_between('one two three four five', 'two', 'four')
        )
        self.assertEqual(
            (None, 16),
            SlurmJob._get_between('one two three four five', 'two', 'four', 16)
        )

    def test_render(self):
        self.assertEqual(wexamples.basic.wdl.strip(), wexamples.basic.info.to_wdl().strip())
        self.assertEqual(wexamples.fastsurfer.wdl.strip(), wexamples.fastsurfer.info.to_wdl().strip())

    def test_from_wdl(self):
        self.assertEqual(wexamples.basic.info, SlurmJob.from_wdl(wexamples.basic.wdl))
        self.assertEqual(wexamples.fastsurfer.info, SlurmJob.from_wdl(wexamples.fastsurfer.wdl))


if __name__ == '__main__':
    unittest.main()
