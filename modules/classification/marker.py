from typing import List, Callable, Any
from dataclasses import dataclass
from typing import Optional, Dict, Literal, Tuple
import re

# Твой тип из предыдущего вопроса
BlockLabel = Literal[
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


@dataclass
class ClassificationResult:
    label: BlockLabel
    confidence: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict

        return asdict(self)


class RuleBasedClassifier:
    """Классификатор блоков документации."""

    def __init__(self):
        # Регистрируем все правила в порядке приоритета (если confidence одинаковый)
        self._rules_colors: List[Tuple[BlockLabel, str]] = [
            ('header', "#FF5733"),
            ('text', "#33FF57"),
            ('image', "#3357FF"),
            ('table', "#FF33A1"),
            ('image_capture', "#A133FF"),
            ('table_capture', "#33FFA1"),
            
        ]

    def classify(
        self, previous_block, current_block, next_block
    ) -> ClassificationResult:

        results: List[ClassificationResult] = []
        if current_block["page"] < 3:
            return ClassificationResult(label="title", confidence=1)
        if current_block["type"] == "table":
            return ClassificationResult(label="table", confidence=1)
        elif current_block["type"] == "image":
            return ClassificationResult(label="image", confidence=1)
        else:
            for rule in self._rules:
                try:
                    result = rule(previous_block, current_block, next_block)
                    if result.confidence > 0:
                        results.append(result)
                except Exception as e:
                    # Логируем ошибку правила, но не ломаем весь классификатор
                    print(f"[WARNING] Ошибка в правиле {rule.__name__}: {e}")

            if not results:
                # На случай если ни одно правило не сработало
                return ClassificationResult(label="text", confidence=0.1)

            # Возвращаем результат с максимальным confidence
            return max(results, key=lambda r: r.confidence)

    # --- ПРАВИЛА КЛАССИФИКАЦИИ ---
