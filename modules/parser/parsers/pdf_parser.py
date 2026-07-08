import fitz
import json
import os


class PdfParser():
    
    def __init__(self):
        self.pt_to_mm = 25.4 / 72
        
    def parse(self, pdf_path: str):
        """Парсит PDF на текстовые блоки, таблицы и изображения в порядке чтения."""
        doc = fitz.open(pdf_path)
        parsed_document = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_width_mm = page.rect.width * self.pt_to_mm
            page_height_mm = page.rect.height * self.pt_to_mm

            # Общий список всех блоков страницы
            all_blocks = []

            # 1. Извлекаем текстовые блоки
            page_dict = page.get_text("dict")
            blocks = page_dict.get("blocks", [])

            for block_idx, block in enumerate(blocks):
                if "lines" not in block:
                    continue

                bbox_mm = [coord * self.pt_to_mm for coord in block["bbox"]]

                block_text = []
                block_fonts = set()
                block_sizes = set()
                lines_y_coords = []

                for line in block["lines"]:
                    lines_y_coords.append(line["bbox"][1] * self.pt_to_mm)

                    for span in line["spans"]:
                        text = span["text"]
                        if text.strip():
                            block_text.append(text)
                            block_fonts.add(span["font"])
                            block_sizes.add(round(span["size"], 1))

                full_text = " ".join(block_text).strip()

                if not full_text:
                    continue

                line_spacing_mm = 0.0
                if len(lines_y_coords) > 1:
                    intervals = [
                        lines_y_coords[i] - lines_y_coords[i - 1]
                        for i in range(1, len(lines_y_coords))
                    ]
                    line_spacing_mm = sum(intervals) / len(intervals)

                block_data = {
                    "type": "text_block",
                    "index": block_idx,
                    "data": {
                         "text": full_text,
                         "typography": {
                            "fonts": list(block_fonts),
                            "sizes_pt": list(block_sizes),
                            "avg_line_spacing_mm": round(line_spacing_mm, 2),
                        },
                    },
                    "geometry": {
                        "left_mm": round(bbox_mm[0], 2),
                        "top_mm": round(bbox_mm[1], 2),
                        "right_mm": round(bbox_mm[2], 2),
                        "bottom_mm": round(bbox_mm[3], 2),
                    },
                }
                all_blocks.append(block_data)

            # 2. Извлекаем таблицы
            try:
                tabs = page.find_tables()
                if tabs and tabs.tables:
                    for table_idx, tab in enumerate(tabs.tables):
                        try:
                            table_data = tab.extract()
                            if table_data:
                                structured_table = {
                                    "type": "table",
                                    "index": table_idx,
                                    "data":{
                                        "rows": len(table_data),
                                        "columns": max(len(row) for row in table_data) if table_data else 0,
                                        "cells": []
                                    }
                                }
                                for row_idx, row in enumerate(table_data):
                                    for col_idx, cell_value in enumerate(row):
                                        if cell_value is not None:
                                            structured_table["data"]["cells"].append({
                                                "row": row_idx,
                                                "column": col_idx,
                                                "text": str(cell_value).strip(),
                                            })
                                
                                bbox = tab.bbox
                                structured_table["geometry"] = {
                                    "left_mm": round(bbox[0] * self.pt_to_mm, 2),
                                    "top_mm": round(bbox[1] * self.pt_to_mm, 2),
                                    "right_mm": round(bbox[2] * self.pt_to_mm, 2),
                                    "bottom_mm": round(bbox[3] * self.pt_to_mm, 2),
                                }
                                all_blocks.append(structured_table)
                        except Exception:
                            continue
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
                        "index": img_idx,
                        "data": {
                            "width": base_image["width"],
                            "height": base_image["height"],
                            "ext": base_image["ext"],
                        }
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
                    image_filename = f"page_{page_num + 1}_img_{img_idx}.{base_image['ext']}"
                    image_path = os.path.join(output_dir, image_filename)
                    
                    with open(image_path, "wb") as f:
                        f.write(base_image["image"])
                    
                    image_data["data"]["saved_path"] = image_path
                    all_blocks.append(image_data)
                    
                except Exception:
                    continue

            # Сортируем ВСЕ блоки вместе по вертикальной позиции (сверху вниз)
            all_blocks.sort(key=lambda b: b["geometry"]["top_mm"])
            
            # Пересчитываем индексы после сортировки
            for new_idx, block in enumerate(all_blocks):
                block["index"] = new_idx

            page_data = {
                "page": page_num + 1,
                "page_size_mm": (round(page_width_mm, 1), round(page_height_mm, 1)),
                "blocks": all_blocks,
            }
            
            parsed_document.append(page_data)
            
        doc.close()
        
        # with open("result_parser.json", "w", encoding="utf-8") as f:
        #     json.dump(parsed_document, f, ensure_ascii=False, indent=4)

        return parsed_document