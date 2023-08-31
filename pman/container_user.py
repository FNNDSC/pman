import random
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ContainerUser:
    """
    Helper for parsing the UID/GID from the ``CONTAINER_USER`` environment variable
    configuration of *pman*.
    """
    uid: None | int | tuple[int, int]
    """Given UID or UID range"""
    gid: None | int | tuple[int, int]
    """Given GID or GID range"""

    @classmethod
    def parse(cls, config_value: Optional[str]) -> 'ContainerUser':
        """Constructor"""
        s = cls._split(config_value)
        uid, gid = map(cls._parse_range, s)
        return cls(uid, gid)

    def get_uid(self) -> Optional[int]:
        """
        Get UID. If UID was given as a range, return a random number in that range.
        """
        return self.__get_value(self.uid)

    def get_gid(self) -> Optional[int]:
        """
        Get GID. If GID was given as a range, return a random number in that range.
        """
        return self.__get_value(self.gid)

    @staticmethod
    def __get_value(s: None | int | tuple[int, int]) -> int:
        if s is None or isinstance(s, int):
            return s
        lo, hi = s
        return random.randint(lo, hi)

    @staticmethod
    def _split(config_value: Optional[str]) -> tuple[str, str]:
        if not config_value:
            config_value = ':'
        split = config_value.split(':')
        if len(split) != 2:
            raise ValueError(f'CONTAINER_USER="{config_value}" does not match format UID:GID')
        left, right = split
        return left, right

    @staticmethod
    def _parse_range(value: str) -> None | int | tuple[int, int]:
        if not value:
            return None
        try:
            lo, hi = map(int, value.split('-'))
            return lo, hi
        except ValueError:
            return int(value)
