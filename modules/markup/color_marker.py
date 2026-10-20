from dataclasses import dataclass, field
from typing import Dict, List
import fitz # type: ignore
from..document import (
    BlockClassifiedType,
    DocumentBlock,
    Document
)

@dataclass
class ColorMarker:
    def markup(self, blocks: List[DocumentBlock], file_path: str, output_path: str):
        doc = fitz.open(file_path)

        for block in blocks:

            page = doc[block.parsed_data.page_parameters.number - 1]
            geometry = block.parsed_data.geometry
            label = block.classified_type.name if block.classified_type else "none"
                
            
            rect = fitz.Rect(
                geometry.left,
                geometry.top,
                geometry.right,
                geometry.bottom,
            )

            page.draw_rect(rect, color=get_color_by_label(block.classified_type), width=1.5)

            page.insert_text(
                point=(geometry.right, geometry.top),
                text=str(label),
                fontsize=10,
                color=(1, 0, 0),   # RGB от 0 до 1 (красный)
                fontname="helv"    
            )

        doc.save(output_path)
        doc.close()

        return doc


def get_color_by_label(label: str) -> tuple[float, float, float]:
    hex_color = BlockClassifiedType.get_color(label)
    if hex_color is None:
        return (0,0,0)
    
    hex_color = hex_color.lstrip('#')

    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    
    return (r, g, b)
