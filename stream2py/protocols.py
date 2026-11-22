"""Defines protocols for classes to avoid circular imports"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Source(Protocol):
    """The interface for the StreamSource class."""

    def key(self, data) -> Any:
        """Sort key of ``data``."""

    @property
    def info(self) -> dict:
        """Information about the source."""
        return {}

    @property
    def sleep_time_on_read_none_s(self) -> int:
        """Seconds to wait when ``read`` returns ``None``."""
        return 0

    def read(self) -> Any:
        """Read the next item, or ``None`` if nothing is ready."""

    def open(self) -> None:
        """Open the resource."""

    def close(self) -> None:
        """Close the resource."""
