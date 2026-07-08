from typing import Any, Dict, List

from .base import BaseClassifier, ClassificationResult


class NeuralClassifier(BaseClassifier):
    """Базовый нейросетевой классификатор.

    Пока это заготовка: метод просто возвращает "unknown" и может быть
    заменён на реальную модель в дальнейшем.
    """

    def __init__(self):
        super().__init__(name="neural")

    def classify(self, blocks: List[Dict[str, Any]]) -> List[ClassificationResult]:
        results: List[ClassificationResult] = []
        for index, block in enumerate(blocks, start=1):
            text = self.extract_text(block)
            if not text:
                label = "empty"
                confidence = 0.0
            else:
                label = "neural_predicted"
                confidence = 0.5

            results.append(
                ClassificationResult(
                    index=index,
                    label=label,
                    confidence=confidence,
                    metadata={"source_type": block.get("type", "unknown")},
                )
            )

        return results
