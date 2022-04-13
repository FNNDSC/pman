from collections import namedtuple
from pman.abstractmgr import Resources
from pman.cromwell.slurm.wdl import SlurmJob, Image, StrWdl

# Since conversion to WDL is lossy, we need to define the
# expected WDL, actual source info, and WDL-converted info (lossy_info)
Example = namedtuple('Example', ['wdl', 'info', 'lossy_info'])

basic = Example(
    wdl=StrWdl(r"""
version 1.0

task plugin_instance {
    command {
        whatsup /share/mr /share/president
    } #ENDCOMMAND
    runtime {
        docker: 'quay.io/fedora/fedora:36'
        sharedir: '/location/of/bribe'
        cpu: '2'
        memory: '5954M'
        gpu_limit: '0'
        number_of_workers: '9'
        timelimit: '12'
    }
}

workflow ChRISJob {
    call plugin_instance
}
"""),
    info=SlurmJob(
        command=['whatsup', '/share/mr', '/share/president'],
        image=Image('quay.io/fedora/fedora:36'),
        sharedir='/location/of/bribe',
        partition=None,
        timelimit=12,
        resources_dict=Resources(
            cpu_limit=1234,
            memory_limit=5678,
            number_of_workers=9,
            gpu_limit=0
        )
    ),
    lossy_info=SlurmJob(
        command=['whatsup', '/share/mr', '/share/president'],
        image=Image('quay.io/fedora/fedora:36'),
        sharedir='/location/of/bribe',
        partition=None,
        timelimit=12,
        resources_dict=Resources(
            cpu_limit=2000,
            memory_limit=5678,
            number_of_workers=9,
            gpu_limit=0
        )
    )
)

fastsurfer = Example(
    wdl=StrWdl(r"""
version 1.0

task plugin_instance {
    command {
        /usr/local/bin/python fastsurfer_inference.py /share/incoming /share/outgoing
    } #ENDCOMMAND
    runtime {
        docker: 'ghcr.io/fnndsc/pl-fastsurfer_inference:1.2.0'
        sharedir: '/neuroimaging/data'
        cpu: '7'
        memory: '10356M'
        gpu_limit: '6'
        number_of_workers: '5'
        timelimit: '300'
        slurm_partition: 'has-gpu'
    }
}

workflow ChRISJob {
    call plugin_instance
}
"""),
    info=SlurmJob(
        command=['/usr/local/bin/python', 'fastsurfer_inference.py', '/share/incoming', '/share/outgoing'],
        image=Image('ghcr.io/fnndsc/pl-fastsurfer_inference:1.2.0'),
        sharedir='/neuroimaging/data',
        partition='has-gpu',
        timelimit=300,
        resources_dict=Resources(
            number_of_workers=5,
            cpu_limit=7000,
            memory_limit=9876,
            gpu_limit=6
        )
    ),
    lossy_info=SlurmJob(
        command=['/usr/local/bin/python', 'fastsurfer_inference.py', '/share/incoming', '/share/outgoing'],
        image=Image('ghcr.io/fnndsc/pl-fastsurfer_inference:1.2.0'),
        sharedir='/neuroimaging/data',
        partition='has-gpu',
        timelimit=300,
        resources_dict=Resources(
            number_of_workers=5,
            cpu_limit=7000,
            memory_limit=9876,
            gpu_limit=6
        )
    )
)
