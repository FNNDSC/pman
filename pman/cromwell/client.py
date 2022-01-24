import io
import json
from dataclasses import dataclass
from typing import Optional, Dict
from .models import (
    WorkflowId, StrWdl,
    WorkflowIdAndStatus, WorkflowQueryResponse, WorkflowMetadataResponse
)
from cromwell_tools.cromwell_api import CromwellAPI, CromwellAuth
from serde.json import from_json


@dataclass
class CromwellClient:
    """
    A wrapper around :mod:`cromwell_tools.cromwell_api` providing a similar
    interface but with typed parameters and returns.
    """
    auth: CromwellAuth

    def submit(self, wdl: StrWdl, label: Dict[str, str]) -> WorkflowIdAndStatus:
        """
        Schedule a WDL file to be executed.

        :param wdl: WDL
        :param label: labels to apply to this workflow
        :return: response from Cromwell
        """
        res = CromwellAPI.submit(
            auth=self.auth,
            wdl_file=self.__str2bytesio(wdl),
            label_file=self.__create_label(label),
            raise_for_status=True
        )
        return from_json(WorkflowIdAndStatus, res.text)

    def status(self, uuid: WorkflowId) -> Optional[WorkflowIdAndStatus]:
        """
        https://cromwell.readthedocs.io/en/stable/api/RESTAPI/#retrieves-the-current-state-for-a-workflow

        :return: workflow ID and status, or None if workflow not found
        """
        res = CromwellAPI.status(uuid=uuid, auth=self.auth, raise_for_status=True)
        if res.status_code == 404:
            return None
        res.raise_for_status()
        return from_json(WorkflowIdAndStatus, res.text)

    def query(self, label: Optional[Dict[str, str]] = None) -> WorkflowQueryResponse:
        query_dict = {}
        if label:
            query_dict['label'] = label
        res = CromwellAPI.query(query_dict=query_dict,
                                auth=self.auth, raise_for_status=True)
        return from_json(WorkflowQueryResponse, res.text)

    def metadata(self, uuid: WorkflowId) -> WorkflowMetadataResponse:
        res = CromwellAPI.metadata(uuid=uuid,
                                   auth=self.auth, raise_for_status=True)
        return from_json(WorkflowMetadataResponse, res.text)

    def abort(self, uuid: WorkflowId) -> WorkflowIdAndStatus:
        """
        https://cromwell.readthedocs.io/en/stable/api/RESTAPI/#abort-a-running-workflow
        """
        res = CromwellAPI.abort(uuid=uuid, auth=self.auth, raise_for_status=True)
        return from_json(WorkflowIdAndStatus, res.text)

    @classmethod
    def __create_label(cls, d: Dict[str, str]) -> io.BytesIO:
        """
        Create Cromwell labels from a dictionary of key-value pairs.

        https://cromwell.readthedocs.io/en/stable/cromwell_features/Labels/
        """
        return cls.__str2bytesio(json.dumps(d))

    @staticmethod
    def __str2bytesio(s: str) -> io.BytesIO:
        return io.BytesIO(bytes(s, 'utf-8'))
