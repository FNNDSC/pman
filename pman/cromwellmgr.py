"""
TODO: another microservice to fill functionality not provided by Cromwell

- manager.get_job_logs --> return stdout
- manager.remove_job --> remove files

"""

import json
import logging
import time
from typing import Optional
from .abstractmgr import AbstractManager, ManagerException, JobStatus, JobInfo, Image, JobName, TimeStamp
from .cromwell.models import (
    WorkflowId, StrWdl,
    WorkflowStatus, WorkflowIdAndStatus, WorkflowQueryResult,
    WorkflowMetadataResponse
)
from .cromwell.client import CromwellAuth, CromwellClient
from .slurmwdl import SlurmJob, SlurmRuntimeAttributes


STATUS_MAP = {
    WorkflowStatus.OnHold: JobStatus.notstarted,
    WorkflowStatus.Submitted: JobStatus.notstarted,
    WorkflowStatus.Running: JobStatus.started,
    WorkflowStatus.Aborted: JobStatus.finishedWithError,
    WorkflowStatus.Aborting: JobStatus.finishedWithError,
    WorkflowStatus.Succeeded: JobStatus.finishedSuccessfully,
    WorkflowStatus.Failed: JobStatus.finishedWithError
}

logger = logging.getLogger(__name__)


class CromwellManager(AbstractManager[WorkflowId]):
    """
    A Cromwell shim for ``pman``.

    https://cromwell.readthedocs.io/

    Instead of defining workflow inputs and outputs, the ``CromwellManager``
    expects for a plugin instance's input files to already exist in the
    remote compute environment's filesystem, and instructs Cromwell to also
    write output files to its filesystem, same as how "storeBase" works with
    the *docker swarm* ``pman`` backend.

    Tip: the workflow name is not the ``pman`` job name! Currently, the
    workflow name is hard-coded for every workflow to be ``ChRISJob``.
    Instead, the ``pman`` job name is tracked by Cromwell as a label with
    the key :const:`PMAN_CROMWELL_LABEL`.
    """

    PMAN_CROMWELL_LABEL = 'org.chrisproject.pman.name'
    """The Cromwell label key for pman job names."""

    def __init__(self, config_dict=None):
        super().__init__(config_dict)
        auth = CromwellAuth(config_dict['CROMWELL_URL'])
        self.__client = CromwellClient(auth)

    def schedule_job(self, image: Image, command: str, name: JobName,
                     resources_dict: dict, mountdir: Optional[str] = None) -> WorkflowId:
        wdl = SlurmJob(image, command, mountdir, resources_dict).to_wdl()
        res = self.__submit(wdl, name)
        # Submission does not appear in Cromwell immediately, but pman wants to
        # get job info, so we need to wait for Cromwell to catch up.
        self.__must_be_submitted(res)
        return res.id

    def __submit(self, wdl: StrWdl, name: JobName) -> WorkflowIdAndStatus:
        """
        Schedule a WDL file to be executed, and then wait for Cromwell to register it.

        :param wdl: WDL
        :param name: ID which pman can be queried for to retrieve the submitted workflow
        :return: response from Cromwell
        """

        res = self.__client.submit(wdl, label={self.PMAN_CROMWELL_LABEL: name})
        self.__must_be_submitted(res)
        if not self.__block_until_metadata_available(res.id):
            raise CromwellException('Workflow was submitted, but timed out waiting for '
                                    f'Cromwell to produce a call on: {res.id}')
        return res

    @staticmethod
    def __must_be_submitted(res: WorkflowIdAndStatus):
        if res.status != WorkflowStatus.Submitted:
            raise CromwellException(f'Workflow status is not "Submitted": {res}')

    def __block_until_metadata_available(self, uuid: WorkflowId, tries=20, interval=1) -> bool:
        """
        Poll for a workflow's metadata until a call has been produced by Cromwell.

        After submitting a workflow, it take a little while for it to register in
        Cromwell, and then it takes a little bit more for it to be parsed, processed,
        and then finally scheduled.

        :param uuid: workflow UUID
        :param tries: number of metadata request attempts
        :param interval: seconds to wait between attempts
        :return: True if a call has been made before timeout, otherwise False
        """
        if tries <= 0:
            return False
        time.sleep(interval)
        if self._check_job_info(uuid) is not None:
            return True
        return self.__block_until_metadata_available(uuid, tries - 1, interval)

    def get_job(self, name: JobName) -> WorkflowId:
        job = self.__query_by_name(name)
        if job:
            return job.id
        raise CromwellException(f'No job found for name="{name}"', status_code=404)

    def get_job_logs(self, job: WorkflowId) -> str:
        # cromwell_tools.utilities.download
        data = self.__client.logs_idc(job)
        return (
            'Logs not yet supported for Cromwell backend. '
            'They can be read manually from here:\n'
            + json.dumps(data, indent=2)
        )

    def get_job_info(self, job: WorkflowId) -> JobInfo:
        info = self._check_job_info(job)
        if info is None:
            raise CromwellException(f'Info not available for WorkflowId={job}', status_code=404)
        return info

    def _check_job_info(self, uuid: WorkflowId) -> Optional[JobInfo]:
        """
        Get job info from Cromwell metadata if available.
        """
        res = self.__client.metadata(uuid)
        if res is None:
            return None
        if self.__is_complete_call(res):
            return self.__info_from_complete_call(res)
        if res.submittedFiles is not None:
            return self.__info_from_early_submission(res)
        return None

    @staticmethod
    def __is_complete_call(res: WorkflowMetadataResponse) -> bool:
        """
        :return: True if metadata shows that Cromwell has picked up and processed the workflow
        """
        return (
                'ChRISJob.plugin_instance' in res.calls
                and len(res.calls['ChRISJob.plugin_instance']) >= 1
                and res.calls['ChRISJob.plugin_instance'][0].commandLine is not None
        )

    @classmethod
    def __info_from_complete_call(cls, res: WorkflowMetadataResponse) -> JobInfo:
        """
        Get info from a workflow which was picked up and processed by Cromwell.
        """
        if len(res.calls['ChRISJob.plugin_instance']) > 1:
            logger.warning('Task "ChRISJob.plugin_instance" has multiple calls: %s', str(res))

        call = res.calls['ChRISJob.plugin_instance'][0]
        attrs = SlurmRuntimeAttributes.deserialize(call.runtimeAttributes)

        return JobInfo(
            name=JobName(res.labels[cls.PMAN_CROMWELL_LABEL]),
            image=attrs.docker,
            cmd=call.commandLine,
            timestamp=res.end if res.end is not None else '',
            message=str(res.status),  # whatever
            status=STATUS_MAP[res.status]
        )

    @classmethod
    def __info_from_early_submission(cls, res: WorkflowMetadataResponse) -> JobInfo:
        """
        Get info from a workflow by parsing its submittedFiles.
        """
        job_details = SlurmJob.from_wdl(res.submittedFiles.workflow)
        labels = json.loads(res.submittedFiles.labels)

        message = 'Waiting to be picked up by Cromwell'
        if 'ChRISJob.plugin_instance' in res.calls and len(res.calls['ChRISJob.plugin_instance']) >= 1:
            message = res.calls['ChRISJob.plugin_instance'][0].executionStatus

        return JobInfo(
            name=labels[cls.PMAN_CROMWELL_LABEL],
            image=job_details.image,
            cmd=job_details.command,
            timestamp=TimeStamp(''),
            message=message,
            status=JobStatus.notstarted
        )

    def __query_by_name(self, name: JobName) -> Optional[WorkflowQueryResult]:
        """
        Get a single job by name.

        :raises CromwellException: if multiple jobs found by the given name
        """
        res = self.__client.query({self.PMAN_CROMWELL_LABEL: name})
        if res.totalResultsCount < 1:
            return None
        if res.totalResultsCount > 1:
            logger.warning('More than one job where name="%s" found in: %s', name, str(res))
            # we will return the first one in the list, which is probably the most recent
        return res.results[0]

    def remove_job(self, job: WorkflowId):
        self.__client.abort(job)


class CromwellException(ManagerException):
    pass
