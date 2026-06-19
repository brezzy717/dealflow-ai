"""Abstract ingestion pipeline contract (fetch → transform → load)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any


class BasePipeline(ABC):
    """Base class every source connector implements."""

    @abstractmethod
    def fetch(self) -> Iterable[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def transform(self, records: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def load(self, records: Iterable[dict[str, Any]]) -> int:
        raise NotImplementedError

    def run(self) -> int:
        raw = list(self.fetch())
        transformed = list(self.transform(raw))
        return self.load(transformed)
