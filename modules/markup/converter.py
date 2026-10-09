from typing import List, Dict, Any
from modules.markup.base import Markup

from ..document import (
    DocumentBlock,
)

def blocks_to_markup(classified_blocks: List[DocumentBlock]) -> List[Markup]:
    """
    Преобразует список классифицированных блоков в инструкции разметки.
    Пропускает блоки без геометрии (например, 'empty') и без результата классификации.
    """
    markups: List[Markup] = []

    for index, block in enumerate(classified_blocks):

        if(block is None): continue

        label = block.normalized_data.relative_space_top
        
            
        
        
        geometry = block.parsed_data.geometry

        if label is None or not geometry:
            continue

        # label = classification.get("label", "unknown")

        # 2. Пропускаем пустые блоки и текст без нарушений (опционально)
        # Если нужно размечать ВСЁ, убери эту проверку
        # if label == "empty":
        #     continue

        # 3. Создаем инструкцию разметки
        markups.append(
            Markup(
                page=block.parsed_data.page_parameters.number,
                geometry={
                    "left": float(geometry.left),
                    "top": float(geometry.top),
                    "right": float(geometry.right),
                    "bottom": float(geometry.bottom),
                },
                label=label,
            )
        )

    return markups
