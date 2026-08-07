"""Transcript + scratchpad memory for agent runs."""
from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional

from .types import Message


class Transcript:
    """Append-only list of Messages with light filtering helpers."""

    def __init__(self) -> None:
        self._messages: List[Message] = []

    def add(self, message: Message) -> None:
        self._messages.append(message)

    def extend(self, messages: List[Message]) -> None:
        self._messages.extend(messages)

    def all(self) -> List[Message]:
        return list(self._messages)

    def by_role(self, role: str) -> List[Message]:
        return [m for m in self._messages if m.role == role]

    def last(self, n: int = 1) -> List[Message]:
        if n <= 0:
            return []
        return list(self._messages[-n:])

    def __len__(self) -> int:
        return len(self._messages)

    def __iter__(self) -> Iterator[Message]:
        return iter(self._messages)


class Scratchpad:
    """Simple key/value store agents can share for structured intermediate data."""

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self._data.get(key, default)

    def update(self, values: Dict[str, Any]) -> None:
        self._data.update(values)

    def snapshot(self) -> Dict[str, Any]:
        return dict(self._data)

    def __contains__(self, key: str) -> bool:
        return key in self._data
