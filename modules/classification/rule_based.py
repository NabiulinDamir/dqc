from typing import List, Callable, Any
from dataclasses import dataclass
from typing import Optional, Dict, Literal
from .base import BaseClassifier, ClassificationResult

# # Твой тип из предыдущего вопроса
# BlockLabel = Literal[
#     "header",
#     "text",
#     "image",
#     "table",
#     "image_capture",
#     "table_capture",
#     "number_list",
#     "marker_list",
#     "empty",
# ]

# @dataclass
# class ClassificationResult:
#     label: BlockLabel
#     confidence: float = 0.0
#     metadata: Optional[Dict[str, Any]] = None

#     def to_dict(self) -> Dict[str, Any]:
#         from dataclasses import asdict

#         return asdict(self)

class RuleBasedClassifier(BaseClassifier):

    def __init__(self):
        super().__init__(name="ml")

    def classify(self, previous_block: Dict[str, Any], current_block: Dict[str, Any], next_block: Dict[str, Any]) -> ClassificationResult:
        return ClassificationResult(
            label="rule_base_class",
            confidence="1",
            metadata={"source_type": current_block.get("type", "unknown")},
        )
