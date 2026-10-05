from typing import Any, Dict, List


from .rule_based import RuleBasedClassifier
from .ml_classifer import MlClassifier

from modules.document import Document, DocumentBlock, BlockParsedType, BlockClassifiedType

def get_classifier(method: str):
    match(method):
        case "ml":
            return MlClassifier()
        case "rule_based":
            return RuleBasedClassifier()
        case _: 
            return RuleBasedClassifier()


def classify_blocks(blocks: List[DocumentBlock], method: str) -> List[DocumentBlock]:
    # Классифицируем все блоки в документе попарно.
    if not blocks: return []

    classifier = get_classifier(method)
    classifed_blocks = classifier.classify(blocks)

    return classifed_blocks


