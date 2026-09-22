from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseNormalizer(ABC):
    """Абстрактная основа для всех нормализаторов."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def normalize(self, block: Dict[str, Any]) -> Dict[str, Any]:
        """Нормализует блок данных."""
        raise NotImplementedError
