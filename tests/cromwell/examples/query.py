from pman.cromwell.models import WorkflowId

expected = WorkflowId('69bec3cb-c2bc-46d3-96a7-8eb15fca2755')

response_text = r"""
{
  "results": [
    {
      "end": "2022-01-23T22:27:58.740Z",
      "id": "69bec3cb-c2bc-46d3-96a7-8eb15fca2755",
      "metadataArchiveStatus": "Unarchived",
      "name": "ChRISJob",
      "start": "2022-01-23T22:27:15.279Z",
      "status": "Succeeded",
      "submission": "2022-01-23T22:27:11.839Z"
    }
  ],
  "totalResultsCount": 1
}
"""
