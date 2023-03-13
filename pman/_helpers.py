from typing import Optional
import docker
from docker import DockerClient

PFCON_STOREBASE_DESTINATION = '/var/local/storeBase'
"""
Path inside pfcon container where the storebase volume is mounted.
"""

def get_storebase_from_docker(pfcon_selector: Optional[str], volume_id: Optional[str]) -> str:
    """
    Use docker (or Podman) to automatically identify a local volume to use as store base.

    The volume name can be given by name. Alternatively, it can be found by trying to detect
    the volume name automatically from pfcon.
    """
    d = docker.from_env()

    if volume_id is not None:
        return get_local_volume_by_id(d, volume_id)

    return get_volume_from_pfcon(d, pfcon_selector)


def get_local_volume_by_id(d: DockerClient, volume_id: str) -> str:
    a = d.volumes.get(volume_id).attrs
    if a['Driver'] != 'local':
        raise ValueError(f'Volume "{a["Name"]}" uses unsupported driver: {a["Driver"]}')
    return a['Mountpoint']


def get_volume_from_pfcon(d: DockerClient, pfcon_selector: str) -> str:
    containers = d.containers.list(filters={'label': pfcon_selector})
    if not containers:
        raise ValueError(f'No container found with label {pfcon_selector}')

    container = containers[0]
    mounts = container.attrs['Mounts']
    mountpoints = (v['Source'] for v in mounts if v['Destination'] == PFCON_STOREBASE_DESTINATION)
    mountpoint = next(mountpoints, None)
    if mountpoint is None:
        raise ValueError(f'Container {container.id} does not have a mount to {PFCON_STOREBASE_DESTINATION}')
    return mountpoint
