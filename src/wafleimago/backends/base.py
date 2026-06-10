"""Backend base class and registry."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class GenerationResult:
    success: bool
    data: bytes | None = None
    format: str = "image/png"
    path: str = ""
    time_seconds: float = 0.0
    model: str = ""
    error: str = ""
    attempts: int = 1


class BaseBackend(ABC):
    name: str = ""
    priority: int = 10

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> GenerationResult: ...

    @abstractmethod
    def list_models(self) -> list[dict[str, Any]]: ...


BACKENDS: dict[str, type[BaseBackend]] = {}
