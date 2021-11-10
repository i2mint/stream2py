"""Typing hints"""
from typing import Optional, Any, Protocol

OpenInstance = Optional[Any]


class ComparableType(Protocol):
    def __lt__(self, other: Any) -> bool:
        ...

    def __gt__(self, other: Any) -> bool:
        ...
