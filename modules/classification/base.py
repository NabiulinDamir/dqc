from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Literal
import re

# import joblib
# from sklearn.feature_extraction.text import TfidfVectorizer
# import pymorphy2
# from nltk.tokenize import WordPunctTokenizer
# from nltk.corpus import stopwords

@dataclass
class ClassificationResult:
    label: Literal[
        "header",
        "text",
        "image",
        "table",
        "image_capture",
        "table_capture",
        "number_list",
        "marker_list",
        "empty",
    ]
    confidence: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
    normalise_block: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# class TrainDocumentInfo: 
#     path: str
#     type: str
#     rules: str

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

    # @abstractmethod
    # def classify(self, previous_block: Dict[str, Any], current_block: Dict[str, Any]) -> ClassificationResult:
    #     """Классифицирует пару блоков и возвращает результат для текущего."""
    #     raise NotImplementedError

    


    
