"""
WDL template for running a *ChRIS* plugin on the BCH *E2* SLURM.

TODO pass resources_dict (requested CPU, mem, GPU, ...) into the WDL task runtime

Maybe it would be nice to set a workflow name instead of just "ChrisPlugin"
but it doesn't really matter.
"""

from typing import Optional, Tuple

from serde import from_dict, deserialize
from jinja2 import Environment
from .abstractmgr import Image, Resources
from pman.cromwell.models import StrWdl, RuntimeAttributes
from dataclasses import dataclass


template = Environment().from_string(r"""
version 1.0

task plugin_instance {
    command {
        {{ cmd }}
    } #ENDCOMMAND
    runtime {
        docker: '{{ docker }}'
        sharedir: '{{ sharedir }}'
    }
}

workflow ChRISJob {
    call plugin_instance
}
""")


@dataclass
class ChRISJob:
    """
    Represents a ChRIS plugin instance which runs on E2.
    """
    image: Image
    command: str
    sharedir: str
    resources_dict: Optional[Resources] = None

    def to_wdl(self) -> StrWdl:
        """
        :return: a WDL wrapper for a *ChRIS* plugin instance
        """
        return StrWdl(template.render(
            cmd=self.command, docker=self.image, sharedir=self.sharedir
        ))

    @classmethod
    def from_wdl(cls, wdl: StrWdl) -> 'ChRISJob':
        command, end = cls._get_between(wdl, 'command {\n', '    } #ENDCOMMAND\n', 35)
        image, end = cls._get_between(wdl, "docker: '", "'\n", end)
        sharedir, _ = cls._get_between(wdl, "sharedir: '", "'\n", end)
        return cls(Image(image), command.strip(), sharedir)

    @staticmethod
    def _get_between(data: str, lookahead: str, lookbehind: str, start: int = 0) -> Tuple[str, int]:
        """
        Some light parsing because miniwdl is not mini at all, and regex is ugly.
        """
        beginning = data.index(lookahead, start) + len(lookahead)
        end = data.index(lookbehind, beginning)
        return data[beginning:end], end


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

    @classmethod
    def deserialize(cls, _a: RuntimeAttributes) -> 'SlurmRuntimeAttributes':
        return from_dict(cls, _a)
