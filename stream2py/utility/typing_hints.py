"""Typing hints"""

from typing import Optional, Any, Protocol

OpenInstance = Optional[Any]


class ComparableType(Protocol):
    """Protocol for keys that support ``<`` and ``>``."""

    def __lt__(self, other: Any) -> bool:
        """Less-than comparison."""

    def __gt__(self, other: Any) -> bool:
        """Greater-than comparison."""
