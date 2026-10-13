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


    def classify(self, blocks: List[DocumentBlock]) -> List[DocumentBlock]:
        for index, block in enumerate(blocks):
            color = block.parsed_data.typography.color if block.parsed_data.typography else "#92384"

            # if index > 0:
            #     prev_type = blocks[index - 1].classified_type
            #     block.normalized_data.prev_block_classified_type = BlockClassifiedType.index(prev_type)
            # else:
            #     block.normalized_data.prev_block_classified_type = BlockClassifiedType.index(BlockClassifiedType.UNKNOWN)
            
            block.classified_type = BlockClassifiedType.get_by_color(color.upper())
        
        return blocks