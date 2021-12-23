from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Source(Protocol):
    """
    >>> 1
    1
    """
    def key(self, data) -> Any:
        ...

    @property
    def info(self) -> dict:
        return {}

    @property
    def sleep_time_on_read_none_s(self) -> int:
        return 0

    def read(self) -> Any:
        ...

    def open(self) -> None:
        ...

    def close(self) -> None:
        ...
