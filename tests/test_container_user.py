import pytest
import random

from pman.container_user import ContainerUser


@pytest.mark.parametrize(
    'value, expected',
    [
        (None, ContainerUser(uid=None, gid=None)),
        ('', ContainerUser(uid=None, gid=None)),
        (':', ContainerUser(uid=None, gid=None)),
        ('1000:', ContainerUser(uid=1000, gid=None)),
        ('1000-1234:', ContainerUser(uid=(1000, 1234), gid=None)),
        ('1000-1234:5678', ContainerUser(uid=(1000, 1234), gid=5678)),
        ('1000-1234:5678-12345', ContainerUser(uid=(1000, 1234), gid=(5678,12345))),
    ]
)
def test_parse_container_user(value: str, expected: ContainerUser):
    assert ContainerUser.parse(value) == expected


def test_get_uid_gid():
    user = ContainerUser(uid=12345, gid=6789)
    assert user.get_uid() == 12345
    assert user.get_gid() == 6789


def test_random_get_uid(example_ranged_user):
    state = random.getstate()
    next_random = random.randint(example_ranged_user.uid[0], example_ranged_user.uid[1])
    random.setstate(state)
    assert example_ranged_user.get_uid() == next_random


def test_random_get_gid(example_ranged_user):
    state = random.getstate()
    next_random = random.randint(example_ranged_user.gid[0], example_ranged_user.gid[1])
    random.setstate(state)
    assert example_ranged_user.get_gid() == next_random


@pytest.fixture
def example_ranged_user() -> ContainerUser:
    return ContainerUser(uid=(1000, 9000000), gid=(1000, 9000000))
