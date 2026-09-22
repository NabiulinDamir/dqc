"""Пакет классификации документов.

Поддерживаются два подхода:
- rule_based: правилоориентированная классификация;
- neural: нейросетевой классификатор.
"""

from .base import BaseClassifier, ClassificationResult
from .rule_based import RuleBasedClassifier
from .ml_classifer import MlClassifier

__all__ = [
    "BaseClassifier",
    "ClassificationResult",
    "RuleBasedClassifier",
    "MlClassifier",
]
