from collections.abc import Callable
from typing import Any


ModelFactory = Callable[[], Any]


class ModelRegistry:
    """Lightweight registry for assembling ensemble model components."""

    def __init__(self) -> None:
        self._registry: dict[str, ModelFactory] = {}

    def register(self, name: str, factory: ModelFactory) -> None:
        self._registry[name] = factory

    def build(self, name: str) -> Any:
        try:
            return self._registry[name]()
        except KeyError as exc:
            raise KeyError(f"Model '{name}' is not registered") from exc

    def list(self) -> list[str]:
        return sorted(self._registry)
