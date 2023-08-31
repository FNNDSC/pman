import os.path

import pytest
import docker
from docker import DockerClient


@pytest.fixture(scope='session')
def docker_client() -> DockerClient:
    return docker.from_env()


@pytest.fixture(scope='session')
def podman_client() -> DockerClient:
    sock = f'unix:///run/user/{os.getuid()}/podman/podman.sock'
    if not os.path.exists(sock):
        raise pytest.skip(f'{sock} not found')
    return docker.DockerClient(base_url=sock)
