"""
Data definitions for Cromwell API responses.
"""
from enum import Enum
from serde import deserialize
from typing import NewType, List, Dict, Optional
from pman.abstractmgr import TimeStamp
from pathlib import Path


StrWdl = NewType('StrWdl', str)
"""WDL as a :type:`str`."""
WorkflowName = NewType('WorkflowName', str)
WorkflowId = NewType('WorkflowId', str)
RuntimeAttributes = Dict[str, str]
"""
Custom information about a task call from Cromwell workflow metadata,
defined by how Cromwell's backend is configured.

p.s. a type alias bc https://github.com/yukinarit/pyserde/issues/192
"""


class WorkflowStatus(Enum):
    """
    https://github.com/broadinstitute/cromwell/blob/32d5d0cbf07e46f56d3d070f457eaff0138478d5/wes2cromwell/src/main/scala/wes2cromwell/WesState.scala#L19-L28
    """

    # btw, the Cromwell documentation is not accurate. It's missing the "On Hold" status.
    # https://broadworkbench.atlassian.net/browse/CROM-6869

    OnHold = 'On Hold'
    Submitted = 'Submitted'
    Running = 'Running'
    Aborting = 'Aborting'
    Aborted = 'Aborted'
    Succeeded = 'Succeeded'
    Failed = 'Failed'


@deserialize
class WorkflowIdAndStatus:
    """
    https://cromwell.readthedocs.io/en/stable/api/RESTAPI/#workflowidandstatus
    """
    id: WorkflowId
    status: WorkflowStatus


@deserialize
class WorkflowQueryResult:
    """
    https://cromwell.readthedocs.io/en/stable/api/RESTAPI/#workflowqueryresult
    """
    end: Optional[TimeStamp]
    id: WorkflowId
    # name will be undefined for the first few seconds after submission
    name: Optional[WorkflowName]
    start: Optional[TimeStamp]
    status: WorkflowStatus
    submission: Optional[TimeStamp]


@deserialize
class WorkflowQueryResponse:
    """
    https://cromwell.readthedocs.io/en/stable/api/RESTAPI/#workflowqueryresponse
    """
    results: List[WorkflowQueryResult]
    totalResultsCount: int


# doesn't seem correct
# @deserialize
# class FailureMessage:
#     """
#     https://cromwell.readthedocs.io/en/stable/api/RESTAPI/#failuremessage
#     """
#     failure: str
#     timestamp: TimeStamp

@deserialize
class CausedFailure:
    message: str
    causedBy: List  # is actually a List['CausedFailure'],
    # but pyserde does not support circular data definition


@deserialize
class CallMetadata:
    """
    https://cromwell.readthedocs.io/en/stable/api/RESTAPI/#callmetadata
    """
    # these are the conventional fields
    backend: Optional[str]
    backendLogs: Optional[dict]
    backendStatus: Optional[str]
    end: Optional[TimeStamp]
    executionStatus: str
    failures: Optional[List[CausedFailure]]
    inputs: Optional[dict]
    jobId: Optional[str]
    returnCode: Optional[int]
    start: Optional[TimeStamp]
    stderr: Optional[Path]
    stdout: Optional[Path]
    # these fields are not documented, yet they are very important
    commandLine: Optional[str]
    runtimeAttributes: Optional[RuntimeAttributes]
    attempt: Optional[int]
    # and these, we don't care about
    # compressedDockerSize: int
    # callCaching: CallCaching
    # shardIndex: int


@deserialize
class SubmittedFiles:
    workflow: StrWdl
    root: str
    options: str
    inputs: str
    workflowUrl: str
    labels: str


@deserialize
class WorkflowMetadataResponse:
    """
    https://cromwell.readthedocs.io/en/stable/api/RESTAPI/#workflowmetadataresponse
    """
    calls: Optional[Dict[str, List[CallMetadata]]]
    end: Optional[TimeStamp]
    failures: Optional[List[CausedFailure]]
    id: WorkflowId
    inputs: Optional[dict]
    outputs: Optional[dict]
    start: Optional[TimeStamp]
    status: WorkflowStatus
    submission: TimeStamp
    # these fields are undocumented
    labels: Dict[str, str]
    submittedFiles: Optional[SubmittedFiles]
