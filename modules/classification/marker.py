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


class MarkerClassifier:
    """Классификатор блоков документации."""

    def __init__(self):
        self._rules_colors: Dict[str, BlockClassifiedType] = {
            "#1F3864": BlockClassifiedType.HEADING         ,
            "#33FF57": BlockClassifiedType.FOOTER          ,
            "#21D6DF": BlockClassifiedType.FORMULA         ,
            "#EE0000": BlockClassifiedType.MARKER_LIST_ITEM,
            "#FFC000": BlockClassifiedType.NUMBER_LIST_ITEM,
            "#ED7D31": BlockClassifiedType.IMAGE_CAPTION   ,
            "#7030A0": BlockClassifiedType.TABLE_CAPTION   ,
            "#000000": BlockClassifiedType.TEXT            ,
            "#106616": BlockClassifiedType.CONTENT_ITEM    ,
            "#DF21BB": BlockClassifiedType.LISTING         ,
            "#32F428": BlockClassifiedType.LISTING_CAPTION         ,
            "#0070C0": BlockClassifiedType.LITERATURE_ITEM 
        }

    def classify(self, blocks: List[DocumentBlock]) -> List[DocumentBlock]:
        for index, block in enumerate(blocks):
            color = block.parsed_data.typography.color if block.parsed_data.typography else "#92384"

            # if index > 0:
            #     prev_type = blocks[index - 1].classified_type
            #     block.normalized_data.prev_block_classified_type = BlockClassifiedType.index(prev_type)
            # else:
            #     block.normalized_data.prev_block_classified_type = BlockClassifiedType.index(BlockClassifiedType.UNKNOWN)
            
            block.classified_type = self._rules_colors.get(color.upper(), BlockClassifiedType.UNKNOWN)
        
        return blocks