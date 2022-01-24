"""
TODO: another microservice to fill functionality not provided by Cromwell

- manager.get_job_logs --> return stdout
- manager.remove_job --> remove files

"""

import logging
import time
from typing import Optional, Tuple
from .abstractmgr import AbstractManager, ManagerException, JobStatus, JobInfo, Image, JobName
from .cromwell.models import (
    WorkflowId, StrWdl,
    WorkflowStatus, WorkflowIdAndStatus, WorkflowQueryResult, WorkflowQueryResponse,
    CallMetadata, WorkflowMetadataResponse
)
from .cromwell.client import CromwellAuth, CromwellClient
from .e2_wdl import inflate_wdl, SlurmRuntimeAttributes, deserialize_runtime_attributes


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
        wdl = inflate_wdl(image, command, resources_dict, mountdir)
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
        if not self.__block_until_called(res.id):
            raise CromwellException('Workflow was submitted, but timed out waiting for '
                                    f'Cromwell to produce a call on: {res.id}')
        return res

    @staticmethod
    def __must_be_submitted(res: WorkflowIdAndStatus):
        if res.status != WorkflowStatus.Submitted:
            raise CromwellException(f'Workflow status is not "Submitted": {res}')

    def __block_until_called(self, uuid: WorkflowId, tries=20, interval=2) -> bool:
        """
        Poll for a workflow's metadata until a call has been produced by Cromwell.

        After submitting a workflow, it take a little while for it to register in
        Cromwell, and then it takes a little bit more for it to be parsed, processed,
        and then finally scheduled.

        :return: True if a call has been made before timeout, otherwise False
        """
        if tries <= 0:
            return False
        time.sleep(interval)
        if self.__call_is_ok(self.__client.metadata(uuid)):
            return True
        return self.__block_until_called(uuid, tries - 1, interval)

    @staticmethod
    def __call_is_ok(res: Optional[WorkflowMetadataResponse]) -> bool:
        """
        :return: True if workflow emtadata exists, has a call, and all calls have a commandLine
        """
        if res is None:
            return False
        # FIXME instead of waiting for a call to be made, parse the submitted
        # WDL file for this information instead.
        # This code should be reused between get_job_info
        if len(res.calls) == 0:
            return False
        calls = [c for task_calls in res.calls.values() for c in task_calls]
        return all(c.commandLine is not None for c in calls)

    def get_job(self, name: JobName) -> WorkflowId:
        job = self.__query_by_name(name)
        if job:
            return job.id
        raise CromwellException(f'No job found for name="{name}"', status_code=404)

    def get_job_logs(self, job: WorkflowId) -> str:
        # cromwell_tools.utilities.download
        return 'Logs from the Cromwell backend not yet implemented.'

    def get_job_info(self, job: WorkflowId) -> JobInfo:
        res = self.__client.metadata(job)
        call, attrs = self.__get_task_from(res)
        return JobInfo(
            name=JobName(res.labels[self.PMAN_CROMWELL_LABEL]),
            image=attrs.docker,
            cmd=call.commandLine,
            timestamp=res.end if res.end is not None else '',
            message=str(res.status),  # whatever
            status=STATUS_MAP[res.status]
        )

    @staticmethod
    def __get_task_from(res: WorkflowMetadataResponse) -> Tuple[CallMetadata, SlurmRuntimeAttributes]:
        """
        Select the task call metadata object along with SLURM job attributes
        from a Cromwell metadata response.
        """
        if len(res.calls) != 1:
            raise CromwellException(f'Number of tasks in this workflow != 1.\n{res}')
        if 'ChRISJob.plugin_instance' not in res.calls:
            raise CromwellException(f'Hard-coded task "ChRISJob.plugin_instance" not found in: {res}')
        if len(res.calls['ChRISJob.plugin_instance']) != 1:
            raise CromwellException(f'Number of calls for task "ChRISJob.plugin_instance" != 1: {res}')
        call = res.calls['ChRISJob.plugin_instance'][0]
        return call, deserialize_runtime_attributes(call.runtimeAttributes)

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
