import io
import json
import unittest
from unittest.mock import Mock, patch, ANY
from pman.abstractmgr import Image, JobName
from pman.cromwellmgr import CromwellManager, CromwellException, WorkflowId
import tests.cromwell.examples.metadata as metadata_example
import tests.cromwell.examples.query as query_example
import functools


def patch_cromwell_api(method_name: str, response_text: str):
    """
    Patch a function of :class:`cromwell_tools.cromwell_api.CromwellAPI`
    so that it returns the given data.

    :param method_name: the function to patch
    :param response_text: the text the mock should respond with
    """
    res = Mock()
    res.text = response_text

    def decorator(real_method):
        @functools.wraps(real_method)
        @patch(f'cromwell_tools.cromwell_api.CromwellAPI.{method_name}')
        def wrapper(self, mock_cromwell_method: Mock, *args, **kwargs):
            mock_cromwell_method.return_value = res
            real_method(self, mock_cromwell_method, *args, **kwargs)
        return wrapper
    return decorator


class CromwellTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.manager = CromwellManager({'CROMWELL_URL': 'https://example.com/'})

    @patch('pman.cromwellmgr.inflate_wdl')
    @patch_cromwell_api('submit', r'{"id": "donut", "status": "Submitted"}')
    def test_submit(self, mock_submit: Mock, mock_inflate_wdl: Mock):
        fake_wdl = 'fake wdl'
        mock_inflate_wdl.return_value = fake_wdl
        self.manager.schedule_job(
            Image('fnndsc/pl-simpledsapp'), 'simpledsapp /in /out',
            JobName('example-jid-4567'), {}, '/storeBase/whatever'
        )
        mock_submit.assert_called_once()
        self.assertBytesIOEqual(fake_wdl, mock_submit.call_args.kwargs['wdl_file'])
        self.assertBytesIOEqualDict(
            {CromwellManager.PMAN_CROMWELL_LABEL: 'example-jid-4567'},
            mock_submit.call_args.kwargs['label_file']
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

    @patch_cromwell_api('abort', r'{"id": "tbh didnt actually try this one", "status": "Aborting"}')
    def test_abort(self, mock_abort: Mock):
        w = WorkflowId('remove-me')
        self.manager.remove_job(w)
        mock_abort.assert_called_once_with(uuid=w, auth=ANY, raise_for_status=True)


if __name__ == '__main__':
    unittest.main()
