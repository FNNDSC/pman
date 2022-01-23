"""
WDL template for running a *ChRIS* plugin on the BCH *E2* SLURM.

TODO pass resources_dict (requested CPU, mem, GPU, ...) into the WDL task runtime

Maybe it would be nice to set a workflow name instead of just "ChrisPlugin"
but it doesn't really matter.
"""

from serde import from_dict, deserialize
from jinja2 import Environment
from .abstractmgr import Image
from pman.cromwell.models import StrWdl, RuntimeAttributes


ds_plugin_template = Environment().from_string(r"""
version 1.0

task plugin_instance {
    command {
        {{ cmd }}
    }
    runtime {
        docker: '{{ docker }}'
        sharedir: '{{ sharedir }}'
    }
}

workflow ChRISJob {
    call plugin_instance
}
""")


@deserialize
class SlurmRuntimeAttributes:
    """
    These fields are custom to how Cromwell is configured to speak with BCH E2 SLURM.
    """
    runtime_minutes: int
    queue: str
    requested_memory_mb_per_core: int
    failOnStderr: bool
    sharedir: str
    continueOnReturnCode: int
    docker: Image
    maxRetries: int
    cpus: int
    account: str


def inflate_wdl(image: Image, command: str,
                resources_dict: dict, mountdir: str) -> StrWdl:
    """
    :return: a WDL wrapper for a *ChRIS* plugin instance
    """
    return StrWdl(ds_plugin_template.render(
        image=image, cmd=command, docker=image, sharedir=mountdir
    ))


def deserialize_runtime_attributes(_a: RuntimeAttributes) -> SlurmRuntimeAttributes:
    return from_dict(SlurmRuntimeAttributes, _a)
