import fitz
import json
import os


class PdfParser:

    def __init__(self):
        self.pt_to_mm = 25.4 / 72

    def parse(self, pdf_path: str):
        """Парсит PDF на текстовые блоки, таблицы и изображения в порядке чтения."""
        doc = fitz.open(pdf_path)

        parsed_document = {
            "blocks": [],
            "pages_info": [],
        }

        # parsed_document = {
        #     "blocks": [
        #         "line":{
        #             "spacing": 0-0

        #         },
        #     ]
        #     "pages_info": [],
        # }

        idx = 0  # Индекс блока в пределах всего документа
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_width_mm = page.rect.width * self.pt_to_mm
            page_height_mm = page.rect.height * self.pt_to_mm

            parsed_document["pages_info"].append(
                {
                    "page": page_num + 1,
                    "page_size_mm": (round(page_width_mm, 1), round(page_height_mm, 1)),
                }
            )

            # 1. Извлекаем текстовые блоки
            page_dict = page.get_text("dict")
            blocks = page_dict.get("blocks", [])

            page_blocks = []
            tmp_text = ""
            for block in blocks:
                if "lines" not in block:
                    continue

                # Накопители
                cur_text = ""
                cur_font = None
                cur_size = None
                cur_bbox = None
                # cur_line_spacings = []  # Список интервалов для расчета среднего
                prev_line_y = None  # Y-координата предыдущей строки
                line_spacing_for_block = 0.0

                for line in block["lines"]:
                    line_top_y = line["bbox"][1] * self.pt_to_mm

                    current_spacing = 0.0
                    if prev_line_y is not None:
                        current_spacing = abs(line_top_y - prev_line_y)
                    line_spacing_for_block = current_spacing

                    for span in line["spans"]:
                        text = span["text"]
                        tmp_text += text
                        if not text.strip():
                            continue

                        f_name = span["font"]
                        f_size = round(span["size"], 1)
                        s_bbox = [c * self.pt_to_mm for c in span["bbox"]]

                        # Проверяем критерии разрыва БЛОКА
                        is_style_changed = False

                        if cur_font is not None:
                            # 1. Смена шрифта/размера
                            if cur_font != f_name or abs(cur_size - f_size) > 0.1:
                                is_style_changed = True

                            elif current_spacing > 0.5:
                                is_style_changed = True

                        if is_style_changed:
                            # Сохраняем ПРЕДЫДУЩИЙ блок
                            # avg_spacing = 0.0
                            # if cur_line_spacings:
                            #     avg_spacing = round(
                            #         sum(cur_line_spacings) / len(cur_line_spacings), 2
                            #     )

                            page_blocks.append(
                                {
                                    "type": "text",
                                    "page": page_num + 1,
                                    "data": {
                                        "text": cur_text.strip(),
                                        "typography": {
                                            "font": cur_font,
                                            "size_pt": cur_size,
                                            "avg_line_spacing_mm": round(line_spacing_for_block, 2),
                                        },
                                    },
                                    "geometry": {
                                        "left_mm": round(cur_bbox[0], 2),
                                        "top_mm": round(cur_bbox[1], 2),
                                        "right_mm": round(cur_bbox[2], 2),
                                        "bottom_mm": round(cur_bbox[3], 2),
                                    },
                                }
                            )

                            # Сброс
                            cur_text = ""
                            cur_bbox = None
                            # cur_line_spacings = []
                            # prev_line_y = None  # Сбрасываем Y, т.к. новая строка - первая в новом блоке

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

                        # Добавляем интервал ТОЛЬКО при переходе на новую строку
                        # if prev_line_y is not None and abs(prev_line_y - line_top_y) > 0.1:
                        #     if current_spacing > 0:
                        #         cur_line_spacings.append(current_spacing)

                    prev_line_y = line_top_y

                # Сохраняем ПОСЛЕДНИЙ блок
                if cur_text.strip():
                    # avg_spacing = 0.0
                    # if cur_line_spacings:
                    #     avg_spacing = round(
                    #         sum(cur_line_spacings) / len(cur_line_spacings), 2
                    #     )
                    page_blocks.append(
                        {
                            "type": "text",
                            "page": page_num + 1,
                            "data": {
                                "text": cur_text.strip(),
                                "typography": {
                                    "font": cur_font,
                                    "size_pt": cur_size,
                                    "avg_line_spacing_mm": round(line_spacing_for_block, 2),
                                },
                            },
                            "geometry": {
                                "left_mm": round(cur_bbox[0], 2),
                                "top_mm": round(cur_bbox[1], 2),
                                "right_mm": round(cur_bbox[2], 2),
                                "bottom_mm": round(cur_bbox[3], 2),
                            },
                        }
                    )
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
                                            "blocks": [],  # СЮДА ПЕРЕМЕСТЯТСЯ ВАШИ ТЕКСТОВЫЕ БЛОКИ
                                            "_bbox_mm": cell_bbox_mm,  # Временное поле для фильтрации
                                        }
                                    )

                            bbox = tab.bbox
                            structured_table["geometry"] = {
                                "left_mm": round(bbox[0] * self.pt_to_mm, 2),
                                "top_mm": round(bbox[1] * self.pt_to_mm, 2),
                                "right_mm": round(bbox[2] * self.pt_to_mm, 2),
                                "bottom_mm": round(bbox[3] * self.pt_to_mm, 2),
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

            # # 3. Извлекаем изображения
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
                            "left_mm": round(rect.x0 * self.pt_to_mm, 2),
                            "top_mm": round(rect.y0 * self.pt_to_mm, 2),
                            "right_mm": round(rect.x1 * self.pt_to_mm, 2),
                            "bottom_mm": round(rect.y1 * self.pt_to_mm, 2),
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

            # Сортируем блоки страницы вместе по вертикальной позиции (сверху вниз)
            page_blocks.sort(key=lambda b: b["geometry"]["top_mm"])

            # Пересчитываем индексы после сортировки
            for block in page_blocks:
                block["index"] = idx
                idx += 1

            parsed_document["blocks"].extend(page_blocks)

        doc.close()

        # with open("result_parser.json", "w", encoding="utf-8") as f:
        #     json.dump(parsed_document, f, ensure_ascii=False, indent=4)

        return parsed_document
