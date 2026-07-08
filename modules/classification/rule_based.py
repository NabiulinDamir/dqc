from typing import Any, Dict, List

from .base import BaseClassifier, ClassificationResult


class RuleBasedClassifier(BaseClassifier):
    """Базовый правилоориентированный классификатор.

    В будущем сюда можно добавить правила по ключевым словам, шаблонам,
    структуре документа и т.д.
    """

    def __init__(self):
        super().__init__(name="rule_based")

    def classify(self, blocks: List[Dict[str, Any]]) -> List[ClassificationResult]:
        results: List[ClassificationResult] = []
        for index, block in enumerate(blocks, start=1):
            text = self.extract_text(block).lower()
            block_type = str(block.get("type", "unknown"))

            if not text:
                label = "empty"
                confidence = 0.0
            elif block_type == "table":
                label = "table"
                confidence = 0.95
            elif block_type == "list_item":
                label = "list"
                confidence = 0.9
            elif any(keyword in text for keyword in ["введение", "заключение", "аннотация"]):
                label = "section"
                confidence = 0.85
            else:
                label = "text"
                confidence = 0.75

            results.append(
                ClassificationResult(
                    index=index,
                    label=label,
                    confidence=confidence,
                    metadata={"source_type": block_type},
                )
            )

        return results
