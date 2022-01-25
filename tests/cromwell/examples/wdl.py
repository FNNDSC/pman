from collections import namedtuple
from pman.slurmwdl import SlurmJob, Image, StrWdl

Example = namedtuple('Example', ['wdl', 'info'])

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
    }
}

workflow ChRISJob {
    call plugin_instance
}
"""),
    info=SlurmJob(
        command='whatsup /share/mr /share/president',
        image=Image('quay.io/fedora/fedora:36'),
        sharedir='/location/of/bribe',
        partition=None,
        resources_dict=None
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
        slurm_partition: 'has-gpu'
    }
}

workflow ChRISJob {
    call plugin_instance
}
"""),
    info=SlurmJob(
        command='/usr/local/bin/python fastsurfer_inference.py /share/incoming /share/outgoing',
        image=Image('ghcr.io/fnndsc/pl-fastsurfer_inference:1.2.0'),
        sharedir='/neuroimaging/data',
        partition='has-gpu',
        resources_dict=None
    )
)
