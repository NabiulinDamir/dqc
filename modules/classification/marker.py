from typing import List, Callable, Any
from dataclasses import dataclass
from typing import Optional, Dict, Literal, Tuple
import re

from ..document import (
    DocumentBlock,
    TextBlockData,
    BlockParsedType,
    BlockClassifiedType
)


class RuleBasedClassifier:
    """Классификатор блоков документации."""

    def __init__(self):
        self._rules_colors: Dict[str, BlockClassifiedType] = [
            ("#FF5733", BlockClassifiedType.HEADING         ),
            ("#33FF57", BlockClassifiedType.FOOTER          ),
            ("#A133FF", BlockClassifiedType.FORMULA         ),
            ("#A133FF", BlockClassifiedType.MARKER_LIST_ITEM),
            ("#A133FF", BlockClassifiedType.NUMBER_LIST_ITEM),
            ("#A133FF", BlockClassifiedType.IMAGE_CAPTION   ),
            ("#A133FF", BlockClassifiedType.TABLE_CAPTION   ),
            ("#A133FF", BlockClassifiedType.TEXT            ),
        ]

    def classify(self, blocks: List[DocumentBlock]):
        for block in blocks:
            color = block.parsed_data.typography.color
            block.classified_type = self._rules_colors.get(color, BlockClassifiedType.UNKNOWN)
    
