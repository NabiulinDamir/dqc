from typing import Any, Dict, List

try:
    from .rule_based import RuleBasedClassifier
    from .neural import NeuralClassifier
except ImportError:  # pragma: no cover - fallback for direct execution
    from rule_based import RuleBasedClassifier
    from neural import NeuralClassifier


def _get_classifier(method: str):
    return NeuralClassifier() if method == "neural" else RuleBasedClassifier()


def classify_pair(previous_block: Dict[str, Any], current_block: Dict[str, Any], method: str = "rule_based", classifier=None) -> str:
    # Классифицируем пару блоков: предыдущий и текущий.
    classifier = classifier or _get_classifier(method)
    return classifier.classify(previous_block, current_block).label


def classify_blocks(blocks: List[Dict[str, Any]], method: str = "rule_based") -> List[Dict[str, Any]]:
    # Классифицируем все блоки в документе попарно.
    if not blocks:
        return []

    classifier = _get_classifier(method)
    enriched_blocks: List[Dict[str, Any]] = []
    previous_block = None

    for block in blocks:
        enriched_block = dict(block)
        if previous_block is None:
            # для первого блока передаем эо же в качестве предыдущего
            enriched_block["classified_type"] = classifier.classify(block, block).label
        else:
            enriched_block["classified_type"] = classify_pair(previous_block, block, method="", classifier=classifier)
        enriched_blocks.append(enriched_block)
        previous_block = enriched_block

    return enriched_blocks


