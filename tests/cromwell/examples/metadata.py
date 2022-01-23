from pman.cromwell.models import WorkflowId, WorkflowStatus
from pman.abstractmgr import JobInfo, JobStatus, Image, TimeStamp, JobName

workflow_uuid = WorkflowId('4165ed81-c121-4a8d-b284-a6dda9ef0aa8')

expected_info = JobInfo(
    name=JobName('example-jid-1234'),
    image=Image('docker.io/fnndsc/pl-office-convert:0.0.1'),
    cmd='office_convert /share/incoming /share/outgoing',
    timestamp=TimeStamp(''),
    message=str(WorkflowStatus.Running),
    status=JobStatus.started
)

response_running = r"""
{
  "workflowName": "ChRISJob",
  "workflowProcessingEvents": [
    {
      "cromwellId": "cromid-fa30812",
      "description": "PickedUp",
      "timestamp": "2022-01-23T19:03:20.147Z",
      "cromwellVersion": "74-10892f4"
    }
  ],
  "actualWorkflowLanguageVersion": "1.0",
  "submittedFiles": {
    "workflow": "version 1.0\n\ntask plugin_instance {\n    command {\n        office_convert /share/incoming /share/outgoing\n    }\n    runtime {\n        docker: 'docker.io/fnndsc/pl-office-convert:0.0.1'\n        sharedir: '/mounted/storebase/example-jid-1234'\n    }\n}\n\nworkflow ChRISJob {\n    call plugin_instance\n}\n",
    "workflowType": "WDL",
    "root": "",
    "workflowTypeVersion": "1.0",
    "options": "{\n\n}",
    "inputs": "{}",
    "workflowUrl": "",
    "labels": "{ \"org.chrisproject.pman.name\": \"example-jid-1234\" }\n"
  },
  "calls": {
    "ChRISJob.plugin_instance": [
      {
        "executionStatus": "Running",
        "stdout": "/cromwell-executions/ChRISJob/4165ed81-c121-4a8d-b284-a6dda9ef0aa8/call-plugin_instance/execution/stdout",
        "backendStatus": "Running",
        "compressedDockerSize": 110900053,
        "commandLine": "office_convert /share/incoming /share/outgoing",
        "shardIndex": -1,
        "runtimeAttributes": {
          "runtime_minutes": "5",
          "queue": "my-slurm-partition",
          "requested_memory_mb_per_core": "4000",
          "failOnStderr": "false",
          "sharedir": "/mounted/storebase/example-jid-1234",
          "continueOnReturnCode": "0",
          "docker": "docker.io/fnndsc/pl-office-convert:0.0.1",
          "maxRetries": "0",
          "cpus": "2",
          "account": "fnndsc"
        },
        "callCaching": {
          "allowResultReuse": false,
          "effectiveCallCachingMode": "CallCachingOff"
        },
        "inputs": {},
        "jobId": "1866268",
        "backend": "SLURM",
        "stderr": "/cromwell-executions/ChRISJob/4165ed81-c121-4a8d-b284-a6dda9ef0aa8/call-plugin_instance/execution/stderr",
        "callRoot": "/cromwell-executions/ChRISJob/4165ed81-c121-4a8d-b284-a6dda9ef0aa8/call-plugin_instance",
        "attempt": 1,
        "start": "2022-01-23T19:03:21.820Z"
      }
    ]
  },
  "outputs": {},
  "workflowRoot": "/cromwell-executions/ChRISJob/4165ed81-c121-4a8d-b284-a6dda9ef0aa8",
  "actualWorkflowLanguage": "WDL",
  "id": "4165ed81-c121-4a8d-b284-a6dda9ef0aa8",
  "inputs": {},
  "labels": {
    "cromwell-workflow-id": "cromwell-4165ed81-c121-4a8d-b284-a6dda9ef0aa8",
    "org.chrisproject.pman.name": "example-jid-1234"
  },
  "submission": "2022-01-23T18:00:49.346Z",
  "status": "Running",
  "start": "2022-01-23T19:03:20.171Z"
}
"""
