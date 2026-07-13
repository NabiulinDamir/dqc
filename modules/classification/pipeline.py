from typing import Any, Dict, List

try:
    from .base import ClassificationResult
    from .rule_based import RuleBasedClassifier
    from .neural import NeuralClassifier
except ImportError:  # pragma: no cover - fallback for direct execution
    from base import ClassificationResult
    from rule_based import RuleBasedClassifier
    from neural import NeuralClassifier


def classify_blocks(
    blocks: List[Dict[str, Any]],
    method: str = "rule_based",
) -> List[Dict[str, Any]]:
    """Общий интерфейс классификации блоков документа.

    Args:
        blocks: список страниц после парсинга или список блоков.
        method: один из вариантов: "rule_based" или "neural".

    Returns:
        Структура, похожая на входную, но с полем classified_type у каждого блока.
    """
    # Выбор подхода классификации: правилоориентированный или нейросетевой
    if method == "neural":
        classifier = NeuralClassifier()
    else:
        classifier = RuleBasedClassifier()

    if not blocks:
        return []

    # Если вход уже имеет структуру "страница -> блоки", классифицируем каждый блок внутри страницы
    if isinstance(blocks[0], dict) and isinstance(blocks[0].get("blocks"), list):
        enriched_pages: List[Dict[str, Any]] = []
        for page in blocks:
            enriched_page = dict(page)
            enriched_page["blocks"] = []
            for block in page.get("blocks", []):
                result = classifier.classify([block])[0]
                enriched_block = dict(block)
                enriched_block["classified_type"] = result.label
                enriched_page["blocks"].append(enriched_block)
            enriched_pages.append(enriched_page)
        return enriched_pages

    results = classifier.classify(blocks)
    enriched_blocks: List[Dict[str, Any]] = []
    for block, result in zip(blocks, results):
        enriched_block = dict(block)
        enriched_block["classified_type"] = result.label
        enriched_blocks.append(enriched_block)

    return enriched_blocks
