from abc import ABC, abstractmethod
from typing import Any, Iterable


class BasePipeline(ABC):
    """Abstract base class for ingestion pipelines."""

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
