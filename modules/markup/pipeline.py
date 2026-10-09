from typing import List
from .base import Markup
import fitz


def markup_document(file_path: str, output_path: str, instructions: List[Markup]) -> fitz.Document:
    doc = fitz.open(file_path)
    MM_TO_PT = 72.0 / 25.4

    for m in instructions:
        page_idx = m.page - 1
        if not (0 <= page_idx < len(doc)):
            continue

        page = doc[page_idx]
        g = m.geometry

        # Прямое обращение к полям — никаких индексов [0], [1]
        rect = fitz.Rect(
            g["left"],
            g["top"],
            g["right"],
            g["bottom"],
        )

        page.draw_rect(rect, color=m.get_color_by_label(), width=1.5)

        page.insert_text(
            point=(g["right"], g["top"]),
            text=str(m.label),
            fontsize=10,
            color=(1, 0, 0),   # RGB от 0 до 1 (красный)
            fontname="helv"    # helv, helv-bold, helv-italic, times, courier
        )

    doc.save(output_path)
    doc.close()

    return doc
