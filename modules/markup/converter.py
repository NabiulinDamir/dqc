from typing import List, Dict, Any
from modules.markup.base import Markup

from ..document import (
    BlockParsedType,
    BlockClassifiedType,
    DocumentBlock,
    ParsedBlockData,
    BlockTypography,
    BlockGeometry,
    PageParameters,
    BlockParsedType,
    NormalizeBlockData,
)

def blocks_to_markup(classified_blocks: List[DocumentBlock]) -> List[Markup]:
    """
    Преобразует список классифицированных блоков в инструкции разметки.
    Пропускает блоки без геометрии (например, 'empty') и без результата классификации.
    """
    markups: List[Markup] = []

    for block in classified_blocks:
        # 1. Проверяем наличие обязательных полей
        label = block.classified_type
        geometry = block.parsed_block_data.geometry

        if not label or not geometry:
            continue

        # label = classification.get("label", "unknown")

        # 2. Пропускаем пустые блоки и текст без нарушений (опционально)
        # Если нужно размечать ВСЁ, убери эту проверку
        if label == "empty":
            continue

        # 3. Создаем инструкцию разметки
        markups.append(
            Markup(
                page=block.parsed_block_data.page_parameters.number,
                geometry={
                    "left_mm": float(geometry.left_mm),
                    "top_mm": float(geometry.top_mm),
                    "right_mm": float(geometry.right_mm),
                    "bottom_mm": float(geometry.bottom_mm),
                },
                label=label,
            )
        )

    return markups
