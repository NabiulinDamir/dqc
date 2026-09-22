import fitz
import json
import os

from ...document import BlockParsed, BlockClassified, DocumentBlock, BlockData, BlockTypography, BlockGeometry, PageParameters

class PdfParser:

    def __init__(self):
        self.pt_to_mm = 25.4 / 72
        self.HEADER_ZONE_LIMIT_MM = 15.0
        self.FOOTER_ZONE_LIMIT_MM = 270.0

    def parse(self, pdf_path: str):
        """Парсит PDF на текстовые блоки, таблицы и изображения в порядке чтения."""
        doc = fitz.open(pdf_path)

        # with open("doc_result_parser.json", "w", encoding="utf-8") as f:
        #     json.dump(doc , f, ensure_ascii=False, indent=4)

        parsed_document = {
            "blocks": [],
            "pages_info": [],
        }

        limit = 1
        idx = 0  # Индекс блока в пределах всего документа
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_width_mm = page.rect.width * self.pt_to_mm
            page_height_mm = page.rect.height * self.pt_to_mm

            parsed_document["pages_info"].append(
                {
                    "number": page_num + 1,
                    "width_mm": round(page_width_mm, 1),
                    "height_mm": round(page_height_mm, 1),
                }
            )

            tmp_page_info = {
                "number": page_num + 1,
                
                "width_mm": round(page_width_mm, 1),
                "height_mm": round(page_height_mm, 1),

                # "text_block_count": 0,
                
                # "avg_font_size": None,
                # "avg_line_spacing": None,
                # "avg_block_height": None,
            }

            tmp_font_sizes = []
            tmp_line_top_spacings = []
            tmp_line_bottom_spacings = []

            # 1. Извлекаем текстовые блоки
            page_dict = page.get_text("dict")
            blocks = page_dict.get("blocks", [])

            page_blocks = []
            tmp_text = ""

            prev_line_y = 0
            for block in blocks:
                if "lines" not in block:
                    continue

                # Накопители
                cur_text = ""
                cur_font = None
                cur_size = None
                cur_bbox = None
                # cur_line_spacings = []  # Список интервалов для расчета среднего
                # Y-координата предыдущей строки
                line_spacing_for_block = 0.0
                height_difference = 0

                footer_blocks = []

                for line in block["lines"]:

                    # height_difference = abs(line_top_y - prev_line_y)

                    # line_spacing_for_block = current_spacing

                    for span in line["spans"]:
                        text = span["text"]
                        tmp_text += text
                        if not text.strip():
                            continue

                        f_name = span["font"]
                        f_size = round(span["size"], 1)

                        tmp_font_sizes.append(f_size)

                        s_bbox = [c * self.pt_to_mm for c in span["bbox"]]
                        t_color_hex = self.getHex(span.get("color", 0))
                        line_top_y = line["bbox"][1] * self.pt_to_mm
                        t_height = line["bbox"][3] * self.pt_to_mm - line["bbox"][1] * self.pt_to_mm
                        height_difference = abs(line_top_y - prev_line_y)

                        # Проверяем критерии разрыва БЛОКА
                        is_style_changed = False

                        if cur_font is not None:
                            # 1. Смена шрифта/размера
                            if cur_font != f_name or abs(cur_size - f_size) > 0.1:
                                # if cur_font
                                is_style_changed = True

                            # 2. Смена высоты строки
                            elif height_difference > (t_height * 0.5):
                                is_style_changed = True

                        if is_style_changed:
                            page_blocks.append(
                                {
                                    "type": "text",
                                    "page": page_num + 1,
                                    "data": {
                                        "text": cur_text.strip(),
                                        "typography": {
                                            "font": cur_font,
                                            "size_pt": cur_size,
                                            "text_color": t_color_hex,
                                            "height_difference": height_difference,
                                        },
                                    },
                                    "geometry": {
                                        "left_mm": int(cur_bbox[0]),
                                        "top_mm": int(cur_bbox[1]),
                                        "right_mm": int(cur_bbox[2]),
                                        "bottom_mm": int(cur_bbox[3]),

                                        "height_mm": t_height,
                                    },
                                }
                            )
                            cur_text = ""
                            cur_bbox = None

                        # Добавляем текст и обновляем состояние
                        cur_text += text
                        cur_font = f_name
                        cur_size = f_size

                        # Обновляем границы
                        if cur_bbox is None:
                            cur_bbox = list(s_bbox)
                        else:
                            cur_bbox[0] = min(cur_bbox[0], s_bbox[0])
                            cur_bbox[1] = min(cur_bbox[1], s_bbox[1])
                            cur_bbox[2] = max(cur_bbox[2], s_bbox[2])
                            cur_bbox[3] = max(cur_bbox[3], s_bbox[3])

                        prev_line_y = line_top_y

                # Сохраняем ПОСЛЕДНИЙ блок
                if cur_text.strip():
                    page_blocks.append(
                        {
                            "type": "text",
                            "page": page_num + 1,
                            "data": {
                                "text": cur_text.strip(),
                                "typography": {
                                    "font": cur_font,
                                    "size_pt": cur_size,
                                    "text_color": t_color_hex,
                                },
                            },
                            "geometry": {
                                "left_mm": int(cur_bbox[0]),
                                "top_mm": int(cur_bbox[1]),
                                "right_mm": int(cur_bbox[2]),
                                "bottom_mm": int(cur_bbox[3]),
                                "huihuihui": None
                            },
                        }
                    )

            # Докидываю среднее значение размера шрифта на страницу, если есть данные

            page_blocks.extend(footer_blocks)

            # if "веб сайтов примерно одинаковые" in tmp_text:
            #     print (tmp_text)
            # tmp_text = ""
            # if "Р.А. Файзрахманов" in tmp_text:
            #     i = 2

            # if(i):
            #     print(tmp_text)
            #     i -= 1
            # tmp_text = ""
            # full_text = " ".join(block_text).strip()

            # line_spacing_mm = 0.0
            # if len(lines_y_coords) > 1:
            #     intervals = [
            #         lines_y_coords[i] - lines_y_coords[i - 1]
            #         for i in range(1, len(lines_y_coords))
            #     ]
            #     line_spacing_mm = sum(intervals) / len(intervals)

            # 2. Извлекаем таблицы и распределяем текстовые блоки по ячейкам
            try:
                tabs = page.find_tables()
                if tabs and tabs.tables:
                    extracted_tables = []

                    for tab in tabs.tables:
                        try:
                            table_data = tab.extract()
                            if not table_data:
                                continue

                            structured_table = {
                                "type": "table",
                                "page": page_num + 1,
                                "data": {
                                    "rows": len(table_data),
                                    "columns": (
                                        max(len(row) for row in table_data)
                                        if table_data
                                        else 0
                                    ),
                                    "cells": [],
                                },
                            }

                            # Собираем bboxes ячеек. tab.cells возвращает плоский список объектов ячеек или bboxes
                            # Сопоставляем их с индексами строк и колонок
                            for row_idx, row in enumerate(table_data):
                                for col_idx, cell_value in enumerate(row):
                                    cell_idx = (
                                        row_idx * structured_table["data"]["columns"]
                                        + col_idx
                                    )

                                    # Проверяем, существует ли ячейка в структуре PyMuPDF
                                    cell_bbox = (
                                        tab.cells[cell_idx]
                                        if cell_idx < len(tab.cells)
                                        else None
                                    )

                                    # Переводим координаты ячейки в mm, чтобы сравнивать с вашей геометрией текстовых блоков
                                    cell_bbox_mm = None
                                    if cell_bbox:
                                        # Если cell_bbox это объект, у него есть кортеж координат, либо это сам кортеж
                                        bbox_coords = (
                                            cell_bbox.bbox
                                            if hasattr(cell_bbox, "bbox")
                                            else cell_bbox
                                        )
                                        cell_bbox_mm = [
                                            coord * self.pt_to_mm
                                            for coord in bbox_coords
                                        ]

                                    structured_table["data"]["cells"].append(
                                        {
                                            "row": row_idx,
                                            "column": col_idx,
                                            "text": (
                                                str(cell_value).strip()
                                                if cell_value is not None
                                                else ""
                                            ),
                                            "blocks": [],  # СЮДА ПЕРЕМЕСТЯТСЯ ТЕКСТОВЫЕ БЛОКИ
                                            "_bbox_mm": cell_bbox_mm,  # Временное поле для фильтрации
                                        }
                                    )

                            bbox = tab.bbox
                            structured_table["geometry"] = {
                                "left_mm": int(bbox[0] * self.pt_to_mm),
                                "top_mm": int(bbox[1] * self.pt_to_mm),
                                "right_mm": int(bbox[2] * self.pt_to_mm),
                                "bottom_mm": int(bbox[3] * self.pt_to_mm),
                            }

                            extracted_tables.append(structured_table)
                        except Exception:
                            continue

                    # --- РАСПРЕДЕЛЕНИЕ ТЕКСТОВЫХ БЛОКОВ ПО ЯЧЕЙКАМ ---
                    standalone_blocks = []

                    for block in page_blocks:
                        # Проверяем только текстовые блоки
                        if block.get("type") != "text":
                            standalone_blocks.append(block)
                            continue

                        geom = block["geometry"]
                        # Считаем центр текстового блока в mm
                        block_center_x = (geom["left_mm"] + geom["right_mm"]) / 2
                        block_center_y = (geom["top_mm"] + geom["bottom_mm"]) / 2

                        assigned_to_cell = False

                        for table in extracted_tables:
                            for cell in table["data"]["cells"]:
                                c_box = cell["_bbox_mm"]
                                if c_box:
                                    # Проверяем, попадает ли центр текстового блока в границы ячейки (в mm)
                                    if (
                                        c_box[0] <= block_center_x <= c_box[2]
                                        and c_box[1] <= block_center_y <= c_box[3]
                                    ):
                                        cell["blocks"].append(block)
                                        assigned_to_cell = True
                                        break
                            if assigned_to_cell:
                                break

                        # Если блок не принадлежит ни одной ячейке, оставляем его на странице
                        if not assigned_to_cell:
                            standalone_blocks.append(block)

                    # Очищаем временные bboxes и переносим таблицы в основной массив
                    for table in extracted_tables:
                        for cell in table["data"]["cells"]:
                            cell.pop("_bbox_mm", None)
                        standalone_blocks.append(table)

                    # Обновляем итоговый массив блоков страницы
                    page_blocks = standalone_blocks

            except Exception:
                pass

            # 3. Извлекаем изображения
            images = page.get_images(full=True)

            for img_idx, img in enumerate(images):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)

                    image_data = {
                        "type": "image",
                        "page": page_num + 1,
                        "data": {
                            "width": base_image["width"],
                            "height": base_image["height"],
                            "ext": base_image["ext"],
                        },
                    }

                    image_rects = page.get_image_rects(xref)
                    if image_rects:
                        rect = image_rects[0]
                        image_data["geometry"] = {
                            "left_mm": int(rect.x0 * self.pt_to_mm),
                            "top_mm": int(rect.y0 * self.pt_to_mm),
                            "right_mm": int(rect.x1 * self.pt_to_mm),
                            "bottom_mm": int(rect.y1 * self.pt_to_mm),
                        }

                    output_dir = "extracted_images"
                    os.makedirs(output_dir, exist_ok=True)
                    image_filename = (
                        f"page_{page_num + 1}_img_{img_idx}.{base_image['ext']}"
                    )
                    image_path = os.path.join(output_dir, image_filename)

                    with open(image_path, "wb") as f:
                        f.write(base_image["image"])

                    image_data["data"]["saved_path"] = image_path
                    page_blocks.append(image_data)

                except Exception:
                    continue

            # --- НАЧАЛО КАСТОМНОЙ СОРТИРОВКИ ПО ПОРЯДКУ ЧТЕНИЯ ---
            # Допуск по вертикали (в мм). Если разница в top_mm меньше этого значения,
            # считаем блоки находящимися на одной строке.
            # 2.5 - 3.0 мм обычно достаточно для учета подстрочных индексов и погрешностей.
            Y_TOLERANCE_MM = 2.5

            # 1. Первичная сортировка по Y, чтобы алгоритм кластеризации работал корректно
            page_blocks.sort(key=lambda b: b["geometry"]["top_mm"])

            lines = []
            current_line = []

            for block in page_blocks:
                if not current_line:
                    current_line.append(block)

                # Берем Y первого блока в текущей строке как эталон (базовую линию)
                ref_y = current_line[0]["geometry"]["top_mm"]
                block_y = block["geometry"]["top_mm"]

                # Если блок в пределах допуска по вертикали - добавляем в текущую строку
                if abs(block_y - ref_y) <= Y_TOLERANCE_MM:
                    current_line.append(block) 
                else:
                    # Иначе сохраняем текущую строку и начинаем новую
                    lines.append(current_line)
                    current_line = [block]

                avg_font_size = round(sum(tmp_font_sizes) / len(tmp_font_sizes), 1)
                block["relative_font_size"] = block.get("data", {}).get("typography", {}).get("size_pt", 0) / avg_font_size

            # Не забываем добавить самую последнюю строку
            if current_line:
                lines.append(current_line)

            # 2. Сортируем блоки ВНУТРИ каждой строки по горизонтали (слева направо)
            for line in lines:
                line.sort(key=lambda b: b["geometry"]["left_mm"])

            # 3. Сплющиваем (flatten) список строк обратно в один плоский список
            page_blocks = [block for line in lines for block in line]

            # --- КОНЕЦ КАСТОМНОЙ СОРТИРОВКИ ---
            parsed_document["blocks"].extend(page_blocks)

        doc.close()

        # with open("result_parser.json", "w", encoding="utf-8") as f:
        #     json.dump(parsed_document, f, ensure_ascii=False, indent=4)

        return parsed_document

    def getHex(self, colorInt: int) -> str:
        r = (colorInt >> 16) & 255
        g = (colorInt >> 8) & 255
        b = colorInt & 255
        return(f"#{r:02x}{g:02x}{b:02x}")
