import io
import json
import unittest
from unittest.mock import Mock, patch, ANY, call
from pman.abstractmgr import Image, JobName
from pman.cromwellmgr import CromwellManager, CromwellException, WorkflowId
import tests.cromwell.examples.metadata as metadata_example
import tests.cromwell.examples.query as query_example
from tests.cromwell.helpers import patch_cromwell_api, create_404_response


class CromwellTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.manager = CromwellManager({'CROMWELL_URL': 'https://example.com/'})

    @patch('time.sleep')
    @patch('pman.cromwellmgr.inflate_wdl')
    @patch('cromwell_tools.cromwell_api.CromwellAPI.status')
    @patch('cromwell_tools.cromwell_api.CromwellAPI.submit')
    def test_submit(self, mock_submit: Mock, mock_status: Mock,
                    mock_inflate: Mock, mock_sleep: Mock):
        # mock WDL template
        fake_wdl = 'fake wdl'
        mock_inflate.return_value = fake_wdl

        # Workflow does not immediately appear in Cromwell after being submitted,
        # but pman wants to get job info, so we need to poll Cromwell a few times.
        ok_res = Mock()
        ok_res.status_code = 200
        ok_res.text = r'{"id": "example-jid-4567", "status": "Submitted"}'
        status_responses = [
            create_404_response('example-jid-4567'),
            create_404_response('example-jid-4567'),
            create_404_response('example-jid-4567'),
            ok_res
        ]
        mock_status.side_effect = status_responses

        mock_submit.return_value = Mock()
        mock_submit.return_value.text = r'{"id": "example-jid-4567", "status": "Submitted"}'

        self.manager.schedule_job(
            Image('fnndsc/pl-simpledsapp'), 'simpledsapp /in /out',
            JobName('example-jid-4567'), {}, '/storeBase/whatever'
        )

        # assert submitted with correct data
        mock_submit.assert_called_once()
        self.assertBytesIOEqual(fake_wdl, mock_submit.call_args.kwargs['wdl_file'])
        self.assertBytesIOEqualDict(
            {CromwellManager.PMAN_CROMWELL_LABEL: 'example-jid-4567'},
            mock_submit.call_args.kwargs['label_file']
        )

        # assert polling worked
        mock_status.assert_has_calls(
            # check that status was polled
            [call(uuid='example-jid-4567', auth=ANY, raise_for_status=False)] * len(status_responses)
        )
        mock_sleep.assert_has_calls(
            # first sleep is a bit longer
            [call(i) for i in [0.5, 0.2, 0.2, 0.2]]
        )

    def assertBytesIOEqual(self, expected: str, actual: io.BytesIO):
        self.assertEqual(expected, self.__bytesIO2str(actual))

    def assertBytesIOEqualDict(self, expected: dict, actual: io.BytesIO):
        self.assertDictEqual(expected, json.loads(self.__bytesIO2str(actual)))

    @staticmethod
    def __bytesIO2str(_b: io.BytesIO) -> str:
        return _b.getvalue().decode('utf-8')

    @patch_cromwell_api('submit', r'{"id": "donut", "status": "On Hold"}')
    def test_submit_bad_response(self, _):
        with self.assertRaises(CromwellException):
            self.manager.schedule_job(
                Image('fnndsc/pl-simpledsapp'), 'simpledsapp /in /out',
                JobName('example-jid-4567'), {}, '/storeBase/whatever'
            )

    @patch_cromwell_api('metadata', metadata_example.response_running)
    def test_get_job_info(self, mock_metadata: Mock):
        job_info = self.manager.get_job_info(metadata_example.workflow_uuid)
        mock_metadata.assert_called_once_with(uuid=metadata_example.workflow_uuid,
                                              auth=ANY, raise_for_status=True)
        self.assertEqual(metadata_example.expected_info, job_info)

    @patch_cromwell_api('query', query_example.response_text)
    def test_get_job(self, mock_query: Mock):
        job_name = JobName('sushi')
        self.assertEqual(query_example.expected, self.manager.get_job(job_name))
        mock_query.assert_called_once_with(
            query_dict={'label': {self.manager.PMAN_CROMWELL_LABEL: 'sushi'}},
            auth=ANY, raise_for_status=True
        )

    @patch_cromwell_api('query', r'{"results": [], "totalResultsCount": 0}')
    def test_get_job_not_found(self, mock_query: Mock):
        with self.assertRaises(CromwellException) as e:
            self.manager.get_job(JobName('sushi'))
        self.assertEqual(404, e.exception.status_code,
                         msg='Should have Exception with status_code=404 when job not found')

    @patch_cromwell_api('abort', r'{"id": "tbh didnt actually try this one", "status": "Aborting"}')
    def test_abort(self, mock_abort: Mock):
        w = WorkflowId('remove-me')
        self.manager.remove_job(w)
        mock_abort.assert_called_once_with(uuid=w, auth=ANY, raise_for_status=True)


if __name__ == '__main__':
    unittest.main()
