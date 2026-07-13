from typing import Any, Dict, List
import re
from .base import BaseClassifier, ClassificationResult


class RuleBasedClassifier(BaseClassifier):
    """Базовый правилоориентированный классификатор.

    В будущем сюда можно добавить правила по ключевым словам, шаблонам,
    структуре документа и т.д.
    """

    def __init__(self):
        super().__init__(name="rule_based")

    def classify(self, previous_block: Dict[str, Any], current_block: Dict[str, Any]) -> ClassificationResult:
        results: List[ClassificationResult] = []
        text = self.extract_text(current_block).lower()
        block_type = str(current_block.get("type", "unknown"))

        if not text:
            label = "empty"
            confidence = 0.0
        elif block_type == "table":
            label = "table"
            confidence = 0.99
        elif block_type == "image":
            label = "image"
            confidence = 0.99
        else:
            if(self.isHeader(previous_block, current_block)):
                label = "header"
            elif(self.isImageCapture(previous_block, current_block)):
                label = "image_capture"
            elif(self.isTableCapture(previous_block, current_block)):
                label = "table_capture"
            elif(self.isNumberList(previous_block, current_block)): 
                label = "number_list"
            elif(self.isMarkerList(previous_block, current_block)):
                label = "marker_list"
            else:
                label = "text"
            confidence = 0.85


        return ClassificationResult(
            label=label, 
            confidence=confidence,
            metadata={"source_type": block_type}
        )
        
        
    def classify_text(self, text: str) -> str:
        return "text" if text.strip() else "empty"
    
    def isHeader(self, previous_block: Dict[str, Any], current_block: Dict[str, Any]) -> bool:
        return "BoldMT" in current_block.get("data").get("typography").get("fonts")[0]

    def isImageCapture(self, previous_block: Dict[str, Any], current_block: Dict[str, Any]) -> bool:
        pattern = r'(?i)^(?:таблица|рис\.?|рисунок)\s*[\.\-\s]*[А-ЯA-Z]?\.?\d+'
        text = current_block.get("data", {}).get("label", "").lower()
        return bool(re.match(pattern, text.strip())) and previous_block.get("type") == "image"
    
    def isTableCapture(self, previous_block: Dict[str, Any], current_block: Dict[str, Any]) -> bool:
        pattern = r'(?i)^таблица\s*[\.\-\s]*[А-ЯA-Z]?\.?\d+'
        text = current_block.get("data", {}).get("label", "").lower()
        return bool(re.match(pattern, text.strip()))
    
    def isNumberList(self, previous_block: Dict[str, Any], current_block: Dict[str, Any]) -> bool:
        pattern = r'^(?:\d+[.\)\-]\s|[А-ЯA-Zа-яa-z][.\)\-]\s|[IVXLCDM]+[.\)\-]\s)'
        text = current_block.get("data", {}).get("label", "").lower()
        return bool(re.match(pattern, text.strip()))
    
    def isMarkerList(self, previous_block: Dict[str, Any], current_block: Dict[str, Any]) -> bool:
        pattern = r'^[\-\•\*\·◦▪▫‣⁃]\s'
        text = current_block.get("data", {}).get("label", "").lower()
        return bool(re.match(pattern, text.strip()))