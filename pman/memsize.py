from dataclasses import dataclass


@dataclass
class Memsize:
    """
    A quantity of bytes.
    """

    mebibytes: int

    def as_mb(self) -> str:
        """Value as megabyte string, ending in 'm'"""
        mb = int(1.048576 * self.mebibytes)
        return f'{mb}m'

    def as_mib(self) -> str:
        """Value as mebibyte string, ending in 'Mi'"""
        return f'{self.mebibytes}Mi'
