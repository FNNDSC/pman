"""
WDL template for running a *ChRIS* plugin on SLURM.

Maybe it would be nice to set a workflow name instead of just "ChrisPlugin"
but it doesn't really matter.
"""

from typing import Optional, Tuple

from serde import from_dict, deserialize
from jinja2 import Environment
from pman.abstractmgr import Image, Resources
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
        {%- if partition %}
        slurm_partition: '{{ partition }}'
        {%- endif %}
    }
}

workflow ChRISJob {
    call plugin_instance
}
""")


@dataclass
class SlurmJob:
    """
    Represents a ChRIS plugin instance which runs on E2.
    """
    image: Image
    command: str
    sharedir: str
    partition: Optional[str] = None
    """https://slurm.schedmd.com/sbatch.html#OPT_partition"""
    resources_dict: Optional[Resources] = None

    def to_wdl(self) -> StrWdl:
        """
        :return: a WDL wrapper for a *ChRIS* plugin instance
        """
        return StrWdl(template.render(
            cmd=self.command, docker=self.image,
            partition=self.partition, sharedir=self.sharedir
        ))

    @classmethod
    def from_wdl(cls, wdl: StrWdl) -> 'SlurmJob':
        command, end = cls._get_between(wdl, 'command {\n', '    } #ENDCOMMAND\n', 35)
        image, end = cls._get_between(wdl, "docker: '", "'\n", end)
        sharedir, end = cls._get_between(wdl, "sharedir: '", "'\n", end)
        partition, _ = cls._get_between(wdl, "slurm_partition: '", "'\n", end)
        return cls(Image(image), command.strip(), sharedir, partition)

    @staticmethod
    def _get_between(data: str, lookahead: str, lookbehind: str, start: int = 0) -> Tuple[Optional[str], int]:
        """
        Some light parsing because miniwdl is not mini at all, and regex is ugly.
        """
        beginning = data.find(lookahead, start)
        if beginning == -1:
            return None, start
        beginning += len(lookahead)
        end = data.index(lookbehind, beginning)
        return data[beginning:end], end


@deserialize
class SlurmRuntimeAttributes:
    """
    These fields are custom to how Cromwell is configured to speak with BCH E2 SLURM.
    """
    runtime_minutes: int
    """
    Execution time limit in minutes

    https://slurm.schedmd.com/sbatch.html#OPT_time
    """
    requested_memory: int
    """
    Memory request in MB

    https://slurm.schedmd.com/sbatch.html#OPT_mem
    """
    cpus: int
    """
    Number of CPUs.

    https://slurm.schedmd.com/sbatch.html#OPT_cpus-per-task
    """
    slurm_partition: str
    """
    SLURM partition name
    
    https://slurm.schedmd.com/sbatch.html#OPT_partition
    """
    slurm_account: str
    """
    SLURM account name

    https://slurm.schedmd.com/sbatch.html#OPT_account
    """

    # pman-specific
    sharedir: str
    docker: Image

    # Cromwell-specific
    failOnStderr: bool
    continueOnReturnCode: int
    maxRetries: int

    @classmethod
    def deserialize(cls, _a: RuntimeAttributes) -> 'SlurmRuntimeAttributes':
        return from_dict(cls, _a)
