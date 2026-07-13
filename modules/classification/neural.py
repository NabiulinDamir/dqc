from typing import Any, Dict

from .base import BaseClassifier, ClassificationResult


class NeuralClassifier(BaseClassifier):
    """Базовый нейросетевой классификатор.

    Пока это заготовка: метод просто возвращает "unknown" и может быть
    заменён на реальную модель в дальнейшем.
    """

    def __init__(self):
        super().__init__(name="neural")

    def classify(self, previous_block: Dict[str, Any], current_block: Dict[str, Any]) -> ClassificationResult:
        text = self.extract_text(current_block)
        if not text:
            label = "empty"
            confidence = 0.0
        else:
            label = "neural_predicted"
            confidence = 0.5

        return ClassificationResult(
            label=label,
            confidence=confidence,
            metadata={"source_type": current_block.get("type", "unknown")}
        )
