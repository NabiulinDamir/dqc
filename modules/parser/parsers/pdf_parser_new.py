import pymupdf
import json
import os

from typing import Any, Dict, List, Optional

from ...document import (
    BlockParsedType,
    BlockClassifiedType,
    DocumentBlock,
    ParsedBlockData,
    BlockTypography,
    BlockGeometry,
    PageParameters,
    NormalizeTextBlockData,
    TextBlockData,
    ImageBlockData
)

class PdfParser:

    def __init__(self):
        self.pt_to_mm = 25.4 / 72
        # self.HEADER_ZONE_LIMIT_MM = 15.0
        # self.FOOTER_ZONE_LIMIT_MM = 270.0

    def parse(self, pdf_path: str):
        """Парсит PDF на текстовые блоки, таблицы и изображения в порядке чтения."""
        doc = pymupdf.open(pdf_path)

        all_blocks: List[DocumentBlock] = []
    
        # ___________ Временные значения документа ___________
        tmp_block_id = 0
        tmp_prev_block = None
        tmp_prev_block_parsed_type = None
        tmp_next_block_parsed_type = None
        # ___________________________________________________

        for page_id in range(doc.page_count):
            page = doc.load_page(page_id)

            page_params = PageParameters(
                number=page_id + 1,
                width_mm=round(page.rect.width, 1),
                height_mm=round(page.rect.height, 1)
            )

            # ___________ Временные значения страницы ___________
            tmp_font_sizes = []

            # ___________________________________________________

            page_blocks = []

            page_dict = page.get_text("dict")
            for block in page_dict.get("blocks", []):

                for line in block.get("lines", []):

                    for span_idx, span in enumerate(line.get("spans", [])):

                        t_text = span.get("text", "").strip()

                        if not t_text: continue

                        t_size = round(span.get("size"), 1)
                        t_font = span.get("font", "")
                        t_color = self.getHex(span.get("color", 0))

                        
                        tmp_font_sizes.append(t_size)

                        # line_top_y = line["bbox"][1] * self.pt_to_mm
                        # t_height = line["bbox"][3] * self.pt_to_mm - line["bbox"][1] * self.pt_to_mm
                        # height_difference = abs(line_top_y - prev_line_y)

                        typography_params = BlockTypography(
                            font_name=t_font,
                            font_size=t_size,
                            color=t_color,
                        )

                        structure_block = DocumentBlock(
                            parsed_type=BlockParsedType.TEXT,
                            parsed_data=ParsedBlockData(
                                data=TextBlockData(text=t_text),
                                typography= typography_params,
                                geometry=BlockGeometry(
                                    left_mm     = span.get("bbox", 0)[0],
                                    right_mm    = span.get("bbox", 0)[2],
                                    top_mm      = span.get("bbox", 0)[1],
                                    bottom_mm   = span.get("bbox", 0)[3]
                                ),
                                page_parameters=page_params,
                            ),
                            normalized_data=NormalizeTextBlockData(
                                has_italic=(typography_params.font_name is not None and "Italic" in typography_params.font_name) and 1 or 0,
                                has_blood = (typography_params.font_name is not None and "Bold" in typography_params.font_name) and 1 or 0,
                                has_capital_start = (t_text[0].isalpha() and t_text[0].isupper()) and 1 or 0,
                                

                            ),
                        )

                        page_blocks.append(structure_block)

            # avg_font_size
            # 2. Извлекаем таблицы и распределяем текстовые блоки по ячейкам
            # try:
            #     tabs = page.find_tables()
            #     if tabs and tabs.tables:
            #         extracted_tables = []

            #         for tab in tabs.tables:
            #             try:
            #                 table_data = tab.extract()
            #                 if not table_data:
            #                     continue

            #                 structured_table = {
            #                     "type": "table",
            #                     "page": page_id + 1,
            #                     "data": {
            #                         "rows": len(table_data),
            #                         "columns": (
            #                             max(len(row) for row in table_data)
            #                             if table_data
            #                             else 0
            #                         ),
            #                         "cells": [],
            #                     },
            #                 }

            #                 # Собираем bboxes ячеек. tab.cells возвращает плоский список объектов ячеек или bboxes
            #                 # Сопоставляем их с индексами строк и колонок
            #                 for row_idx, row in enumerate(table_data):
            #                     for col_idx, cell_value in enumerate(row):
            #                         cell_idx = (
            #                             row_idx * structured_table["data"]["columns"]
            #                             + col_idx
            #                         )

            #                         # Проверяем, существует ли ячейка в структуре PyMuPDF
            #                         cell_bbox = (
            #                             tab.cells[cell_idx]
            #                             if cell_idx < len(tab.cells)
            #                             else None
            #                         )

            #                         # Переводим координаты ячейки в mm, чтобы сравнивать с вашей геометрией текстовых блоков
            #                         cell_bbox_mm = None
            #                         if cell_bbox:
            #                             # Если cell_bbox это объект, у него есть кортеж координат, либо это сам кортеж
            #                             bbox_coords = (
            #                                 cell_bbox.bbox
            #                                 if hasattr(cell_bbox, "bbox")
            #                                 else cell_bbox
            #                             )
            #                             cell_bbox_mm = [
            #                                 coord * self.pt_to_mm
            #                                 for coord in bbox_coords
            #                             ]

            #                         structured_table["data"]["cells"].append(
            #                             {
            #                                 "row": row_idx,
            #                                 "column": col_idx,
            #                                 "text": (
            #                                     str(cell_value).strip()
            #                                     if cell_value is not None
            #                                     else ""
            #                                 ),
            #                                 "blocks": [],  # СЮДА ПЕРЕМЕСТЯТСЯ ТЕКСТОВЫЕ БЛОКИ
            #                                 "_bbox_mm": cell_bbox_mm,  # Временное поле для фильтрации
            #                             }
            #                         )

            #                 bbox = tab.bbox
            #                 structured_table["geometry"] = {
            #                     "left_mm": int(bbox[0] * self.pt_to_mm),
            #                     "top_mm": int(bbox[1] * self.pt_to_mm),
            #                     "right_mm": int(bbox[2] * self.pt_to_mm),
            #                     "bottom_mm": int(bbox[3] * self.pt_to_mm),
            #                 }

            #                 extracted_tables.append(structured_table)
            #             except Exception:
            #                 continue

            #         # --- РАСПРЕДЕЛЕНИЕ ТЕКСТОВЫХ БЛОКОВ ПО ЯЧЕЙКАМ ---
            #         standalone_blocks = []

            #         for block in page_blocks:
            #             # Проверяем только текстовые блоки
            #             if block.get("type") != "text":
            #                 standalone_blocks.append(block)
            #                 continue

            #             geom = block["geometry"]
            #             # Считаем центр текстового блока в mm
            #             block_center_x = (geom["left_mm"] + geom["right_mm"]) / 2
            #             block_center_y = (geom["top_mm"] + geom["bottom_mm"]) / 2

            #             assigned_to_cell = False

            #             for table in extracted_tables:
            #                 for cell in table["data"]["cells"]:
            #                     c_box = cell["_bbox_mm"]
            #                     if c_box:
            #                         # Проверяем, попадает ли центр текстового блока в границы ячейки (в mm)
            #                         if (
            #                             c_box[0] <= block_center_x <= c_box[2]
            #                             and c_box[1] <= block_center_y <= c_box[3]
            #                         ):
            #                             cell["blocks"].append(block)
            #                             assigned_to_cell = True
            #                             break
            #                 if assigned_to_cell:
            #                     break

            #             # Если блок не принадлежит ни одной ячейке, оставляем его на странице
            #             if not assigned_to_cell:
            #                 standalone_blocks.append(block)

            #         # Очищаем временные bboxes и переносим таблицы в основной массив
            #         for table in extracted_tables:
            #             for cell in table["data"]["cells"]:
            #                 cell.pop("_bbox_mm", None)
            #             standalone_blocks.append(table)

            #         # Обновляем итоговый массив блоков страницы
            #         page_blocks = standalone_blocks

            # except Exception:
            #     pass

            # 3. Извлекаем изображения
            images = page.get_images(full=True)

            for img_idx, img in enumerate(images):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)

                    image_rects = page.get_image_rects(xref)

                    output_dir = "extracted_images"
                    os.makedirs(output_dir, exist_ok=True)
                    image_filename = (
                        f"page_{page_id + 1}_img_{img_idx}.{base_image['ext']}"
                    )
                    image_path = os.path.join(output_dir, image_filename)

                    with open(image_path, "wb") as f:
                        f.write(base_image["image"])

                    block = DocumentBlock(
                        parsed_type=BlockParsedType.IMAGE,
                        parsed_data=ParsedBlockData(
                            data=ImageBlockData(
                                width_mm=base_image["width"],
                                height_mm=base_image["height"],
                                ext=base_image["ext"],
                                saved_path=image_path,
                            ),
                            geometry=BlockGeometry(
                                left_mm=int(image_rects[0].x0),
                                right_mm=int(image_rects[0].x1),
                                top_mm=int(image_rects[0].y0),
                                bottom_mm=int(image_rects[0].y1),
                            ),
                            page_parameters=page_params
                        ),
                        normalized_data=NormalizeTextBlockData()
                    )

                    page_blocks.append(block)

                except Exception:
                    continue

            # --- НАЧАЛО КАСТОМНОЙ СОРТИРОВКИ ПО ПОРЯДКУ ЧТЕНИЯ ---
            # Допуск по вертикали (в мм). Если разница в top_mm меньше этого значения,
            # считаем блоки находящимися на одной строке.
            # 2.5 - 3.0 мм обычно достаточно для учета подстрочных индексов и погрешностей.
            Y_TOLERANCE_MM = 2.5

            def get_center_y(block: DocumentBlock) -> float:
                return (block.parsed_data.geometry.top_mm + block.parsed_data.geometry.bottom_mm) / 2
            
            # Сортируем по центру Y
            sorted_blocks = sorted(page_blocks, key=get_center_y)
            
            lines = []
            current_line = [sorted_blocks[0]]
            current_line_y = get_center_y(sorted_blocks[0])
            
            for block in sorted_blocks[1:]:
                block_y = get_center_y(block)
                
                # Если центр блока близок к центру линии — та же строка
                if abs(block_y - current_line_y) <= Y_TOLERANCE_MM:
                    current_line.append(block)
                else:
                    lines.append(current_line)
                    current_line = [block]
                    current_line_y = block_y
            
            if current_line:
                lines.append(current_line)
            
            # Сортируем внутри линий по left
            for line in lines:
                line.sort(key=lambda b: b.parsed_data.geometry.left_mm)
            
            # Сплющиваем
            for line_idx, line in enumerate(lines):
                for block_idx, block in enumerate(line):

                    block.id = tmp_block_id
                    block.normalized_data.prev_block_parsed_type = list(BlockParsedType).index(BlockParsedType(tmp_prev_block_parsed_type)) if tmp_prev_block_parsed_type else 0
                    if tmp_prev_block: tmp_prev_block.normalized_data.next_block_parsed_type = list(BlockParsedType).index(BlockParsedType(block.parsed_type))
                    block.normalized_data.position_in_line = block_idx + 1
                    
                    all_blocks.append(block)

                    
                    tmp_prev_block_parsed_type = block.parsed_type
                    tmp_prev_block = block
                    tmp_block_id += 1






        # with open("result_parser.json", "w", encoding="utf-8") as f:
        #     json.dump(parsed_document, f, ensure_ascii=False, indent=4)
        doc.close()
        return all_blocks

    # def getTextBlocks(self, page) -> List[DocumentBlock]:

    def getHex(self, colorInt: int) -> str:
        r = (colorInt >> 16) & 255
        g = (colorInt >> 8) & 255
        b = colorInt & 255
        return(f"#{r:02x}{g:02x}{b:02x}")
