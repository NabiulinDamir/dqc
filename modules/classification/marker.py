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
            color = "#922384"
            if isinstance(block.parsed_data.data, TextBlockData):
                if block.parsed_data.data.typography:
                    color = block.parsed_data.data.typography.color
            else:
                # Для таблиц, изображений и других нетекстовых блоков
                # можно вернуть дефолт или определить цвет по типу блока
                pass
            block.classified_type = BlockClassifiedType.get_by_color(color.upper())
        
        return blocks