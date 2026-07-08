from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class ClassificationResult:
    index: int
    label: str
    confidence: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaseClassifier(ABC):
    """Абстрактная основа для всех классификаторов."""

    def __init__(self, name: str):
        self.name = name

    def extract_text(self, block: Dict[str, Any]) -> str:
        """Извлекает текст из структуры блока."""
        content = block.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

        data = block.get("data")
        if isinstance(data, dict):
            text = data.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()

            nested_content = data.get("content")
            if isinstance(nested_content, str) and nested_content.strip():
                return nested_content.strip()

            cells = data.get("cells")
            if isinstance(cells, list):
                parts = []
                for cell in cells:
                    if isinstance(cell, dict):
                        cell_text = cell.get("text")
                        if isinstance(cell_text, str) and cell_text.strip():
                            parts.append(cell_text.strip())
                if parts:
                    return " ".join(parts)

        return ""

    @abstractmethod
    def classify(self, blocks: List[Dict[str, Any]]) -> List[ClassificationResult]:
        """Классифицирует список блоков и возвращает результаты."""
        raise NotImplementedError
