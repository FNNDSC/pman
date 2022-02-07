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


# Some of these runtime attributes come from the convention here:
# https://cromwell.readthedocs.io/en/stable/RuntimeAttributes/
template = Environment().from_string(r"""
version 1.0

task plugin_instance {
    command {
        {{ cmd }}
    } #ENDCOMMAND
    runtime {
        docker: '{{ docker }}'
        sharedir: '{{ sharedir }}'
        cpu: '{{ (cpu_limit / 1000)|round(method='ceil')|int }}'
        memory: '{{ (memory_limit * 1.048576)|round(method='ceil')|int }}M'
        gpus_per_task: '{{ gpu_limit }}'
        number_of_workers: '{{ number_of_workers }}'
        timelimit: '{{ timelimit }}'
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

    Conversion to WDL is lossy because CPU needs to be converted from
    milicores to cores, and memory needs to be converted from MiB to MB.
    """
    image: Image
    command: str
    sharedir: str
    resources_dict: Resources
    timelimit: int
    partition: Optional[str] = None
    """https://slurm.schedmd.com/sbatch.html#OPT_partition"""

    def to_wdl(self) -> StrWdl:
        """
        :return: a WDL wrapper for a *ChRIS* plugin instance
        """
        return StrWdl(template.render(
            cmd=self.command, docker=self.image,
            partition=self.partition, sharedir=self.sharedir,
            timelimit=self.timelimit,
            **self.resources_dict
        ))

    @classmethod
    def from_wdl(cls, wdl: StrWdl) -> 'SlurmJob':
        """
        Parses a WDL created by :meth:`SlurmJob.to_wdl`. The format + whitespace
        must be exact.
        """
        command, end = cls._get_between(wdl, 'command {\n', '    } #ENDCOMMAND\n', 35)
        image, end = cls._get_resource(wdl, 'docker', end)
        sharedir, end = cls._get_resource(wdl, 'sharedir', end)
        cpu, end = cls._get_resource(wdl, 'cpu', end)
        memory, end = cls._get_resource(wdl, 'memory', end)
        gpus_per_task, end = cls._get_resource(wdl, 'gpus_per_task', end)
        number_of_workers, end = cls._get_resource(wdl, 'number_of_workers', end)
        timelimit, end = cls._get_resource(wdl, 'timelimit', end)
        partition, _ = cls._find_between(wdl, "slurm_partition: '", "'\n", end)
        r = Resources(
            number_of_workers=int(number_of_workers),
            cpu_limit=cls.__serialize_cpu(cpu),
            memory_limit=cls.__serialize_mem(memory),
            gpu_limit=int(gpus_per_task)
        )
        return cls(Image(image), command.strip(), sharedir, r, int(timelimit), partition)

    @staticmethod
    def __serialize_cpu(_c: str) -> int:
        """
        Cores to milicores
        """
        return int(_c) * 1000

    @staticmethod
    def __serialize_mem(_m: str) -> int:
        """
        MB to MiB
        """
        if not _m.endswith('M'):
            raise ValueError('Memory value must end with "M"')
        return int(int(_m[:-1]) * 0.95367432)

    @classmethod
    def _get_resource(cls, wdl: StrWdl, name: str, end: int) -> Tuple[str, int]:
        return cls._get_between(wdl, f"{name}: '", "'\n", end)

    @classmethod
    def _get_between(cls, data: str, lookahead: str, lookbehind: str, start: int = 0) -> Tuple[str, int]:
        value, end = cls._find_between(data, lookahead, lookbehind, start)
        if not value:
            raise ValueError(f'"{lookahead}" not found in: {data}')
        return value, end

    @staticmethod
    def _find_between(data: str, lookahead: str, lookbehind: str, start: int = 0) -> Tuple[Optional[str], int]:
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
    timelimit: int
    """
    Execution time limit in minutes

    https://slurm.schedmd.com/sbatch.html#OPT_time
    """
    memory: int
    """
    Memory request in MB

    https://slurm.schedmd.com/sbatch.html#OPT_mem
    """
    cpu: int
    """
    Number of CPUs.

    https://slurm.schedmd.com/sbatch.html#OPT_cpus-per-task
    """
    slurm_partition: str
    """
    SLURM partition name
    
    https://slurm.schedmd.com/sbatch.html#OPT_partition
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
