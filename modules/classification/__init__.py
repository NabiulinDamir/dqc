"""Пакет классификации документов.

Поддерживаются два подхода:
- rule_based: правилоориентированная классификация;
- neural: нейросетевой классификатор.
"""

from .base import BaseClassifier, ClassificationResult
from .rule_based import RuleBasedClassifier
from .neural import NeuralClassifier

__all__ = [
    "BaseClassifier",
    "ClassificationResult",
    "RuleBasedClassifier",
    "NeuralClassifier",
]
