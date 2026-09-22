from typing import Any, Dict, List


from .rule_based import RuleBasedClassifier
from .ml_classifer import MlClassifier


# from .base import create_dictionary, TrainDocumentInfo

def _get_classifier(method: str):
    match(method):
        case "ml":
            return MlClassifier()
        case "rule_based":
            return RuleBasedClassifier()
        case _: 
            return RuleBasedClassifier()


# def classify_one_block(previous_block: Dict[str, Any], current_block: Dict[str, Any], next_block: Dict[str, Any], method: str) -> str:
#     classifier = classifier or _get_classifier(method)
#     return classifier.classify(previous_block, current_block, next_block).normalise_block

# def classify_all_block(blocks: List[Dict[str, Any]], method: str) -> str:
#     classifier = classifier or _get_classifier(method)
#     return classifier.classify(blocks)


def classify_blocks(blocks: List[Dict[str, Any]], method: str) -> List[Dict[str, Any]]:
    # Классифицируем все блоки в документе попарно.
    if not blocks:
        return []

    classifier = _get_classifier(method)

    classifed_blocks = classifier.classify(blocks)

    # previous_block = None
    # current_block = None
    # next_block = None

    # print(len(blocks))

    # blocks.append(None)
    # for block in blocks:

    #     previous_block = current_block
    #     current_block = next_block
    #     next_block = block

    #     if current_block is None: continue

    #     classifed_block = dict(current_block)
    #     # print(current_block)
    #     classifed_block["classification_result"] = classify_one_block(
    #         previous_block, current_block, next_block, method="", classifier=classifier
    #     )
    #     classifed_blocks.append(classifed_block)

    return classifed_blocks


def train_ml_classifer(blocks: List[Dict[str, Any]]):
    print("Начало обучения")
    classifier = _get_classifier("ml")
    classifier.train(blocks)
