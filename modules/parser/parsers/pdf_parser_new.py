import pymupdf
import json
import os
import statistics
from typing import Any, Dict, List, Optional, Tuple

from ...document import (
    BlockParsedType,
    BlockClassifiedType,
    DocumentBlock,
    ParsedBlockData,
    TextTypography,
    BlockGeometry,
    PageParameters,
    NormalizeTextBlockData,
    TextBlockData,
    ImageBlockData,
    TableCell,
    TableBlockData,
)

class PdfParser:

    def __init__(self):
        self.pt_to = 25.4 / 72
        # self.HEADER_ZONE_LIMIT_MM = 15.0
        # self.FOOTER_ZONE_LIMIT_MM = 270.0
        self.tmp_font_sizes = []
        self.tmp_left_paddings = []

        self.doc = None

    def parse(self, pdf_path: str):
        """Парсит PDF на текстовые блоки, таблицы и изображения в порядке чтения."""
        self.doc = pymupdf.open(pdf_path)

        all_blocks: List[DocumentBlock] = []
    
        # ___________ Временные значения документа ___________
        tmp_block_id = 0
        tmp_prev_block = None
        tmp_prev_block_parsed_type = None
        tmp_next_block_parsed_type = None


        # ___________________________________________________

        for page_id in range(self.doc.page_count):
            page = self.doc.load_page(page_id)

            page_params = PageParameters(
                number=page_id + 1,
                width=round(page.rect.width, 1),
                height=round(page.rect.height, 1)
            )

            page_blocks = []


            self.extract_text_from_page(
                page=page,
                page_blocks=page_blocks,
                page_params=page_params,
            )

            self.extract_images_from_page(
                page=page,
                page_blocks=page_blocks,
                page_params=page_params,
            )

            self.extract_tables_from_page(
                page=page,
                page_blocks=page_blocks,
                page_params=page_params,
            )
            

            # 3. Извлекаем изображения
            


            # --- НАЧАЛО КАСТОМНОЙ СОРТИРОВКИ ПО ПОРЯДКУ ЧТЕНИЯ ---
            # Допуск по вертикали (в мм). Если разница в top меньше этого значения,
            # считаем блоки находящимися на одной строке.
            # 2.5 - 3.0 мм обычно достаточно для учета подстрочных индексов и погрешностей.
            Y_TOLERANCE_MM = 2.5


            # ___________ Временные значения страницы ___________
            median_font_size = sorted(self.tmp_font_sizes)[len(self.tmp_font_sizes) // 2] if self.tmp_font_sizes else 12
            median_left_paddings = sorted(self.tmp_left_paddings)[len(self.tmp_left_paddings) // 2] if self.tmp_left_paddings else 12

            tmp_prev_line_top = 0
            tmp_prev_line_bottom = 0
            # ___________________________________________________



            def get_center_y(block: DocumentBlock) -> float:
                return (block.parsed_data.geometry.top + block.parsed_data.geometry.bottom) / 2
            
            # Сортируем по центру Y
            sorted_blocks: List[DocumentBlock] = sorted(page_blocks, key=get_center_y)
            
            lines: List[List[DocumentBlock]]= []
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
                line.sort(key=lambda b: b.parsed_data.geometry.left)
            
            # Сплющиваем
            lines_count = len(lines)

            for line_idx, line in enumerate(lines):
                block_count = len(line)
                # if(line_idx < len(lines) - 1):
                    # tmp_next_line_top = statistics.mean(block.parsed_data.geometry.bottom for block in lines[line_idx + 1]) 
                
                for block_idx, block in enumerate(line):

                    block.id = tmp_block_id
                    block.normalized_data.prev_block_parsed_type = list(BlockParsedType).index(BlockParsedType(tmp_prev_block_parsed_type)) if tmp_prev_block_parsed_type else 0
                    
                    if tmp_prev_block: 
                        tmp_prev_block.normalized_data.next_block_parsed_type = list(BlockParsedType).index(BlockParsedType(block.parsed_type))

                    block.normalized_data.position_in_page = round((line_idx) / (lines_count - 1), 2)

                    block.parsed_data.geometry.margin_top = round(block.parsed_data.geometry.top - tmp_prev_line_bottom, 0)
                    # block.parsed_data.geometry.margin_bottom = round((tmp_next_line_top or block.parsed_data.page_parameters.height) - block.parsed_data.geometry.bottom, 0)
                    block.parsed_data.geometry.margin_left = round(block.parsed_data.geometry.left - (line[block_idx - 1].parsed_data.geometry.right if block_idx > 0 else 0), 0)

                    if(block.parsed_type == BlockParsedType.TEXT):
                        block.normalized_data.position_in_line = round(block_idx / (block_count - 1), 2) if block_count > 1 else 0.0
                        block.normalized_data.relative_font_size    = round(block.parsed_data.data.typography.font_size / median_font_size, 2)
                        
                        
                        
                    all_blocks.append(block)

                    
                    tmp_prev_block_parsed_type = block.parsed_type
                    tmp_prev_block = block
                    tmp_block_id += 1
                
                tmp_prev_line_bottom = statistics.mean(block.parsed_data.geometry.bottom for block in line)
                


    


        # with open("result_parser.json", "w", encoding="utf-8") as f:
        #     json.dump(parsed_document, f, ensure_ascii=False, indent=4)
        self.doc.close()
        return all_blocks

    # def getTextBlocks(self, page) -> List[DocumentBlock]:

# endregion
# ============================================================
# region Текст
# ============================================================
    def extract_text_from_page(
        self,
        page: pymupdf.Page,
        page_blocks: List[DocumentBlock],
        page_params: PageParameters,
    ):
        page_dict = page.get_text("dict")
        for block in page_dict.get("blocks", []):

            for line in block.get("lines", []):

                for span_idx, span in enumerate(line.get("spans", [])):

                    t_text = span.get("text", "").strip()

                    if not t_text: continue

                    t_size = round(span.get("size"), 1)
                    t_font = span.get("font", "")
                    t_color = _get_hex(span.get("color", 0))

                    self.tmp_font_sizes.append(t_size)
                    self.tmp_left_paddings.append(span.get("bbox", 0)[0])

                    p_left     = span.get("bbox", 0)[0]
                    p_right    = span.get("bbox", 0)[2]
                    p_top      = span.get("bbox", 0)[1]
                    p_bottom   = span.get("bbox", 0)[3]


                    typography_params = TextTypography(
                        font_name=t_font,
                        font_size=t_size,
                        color=t_color,
                    )

                    structure_block = DocumentBlock(
                        parsed_type=BlockParsedType.TEXT,
                        parsed_data=ParsedBlockData(
                            data=TextBlockData(
                                text=t_text,
                                typography= typography_params,
                            ), 
                            geometry=BlockGeometry(
                                left   = p_left,
                                right  = p_right,
                                top    = p_top,
                                bottom = p_bottom 
                            ),
                            page_parameters=page_params,
                        ),
                        normalized_data=NormalizeTextBlockData(
                            has_italic=(typography_params.font_name is not None and "Italic" in typography_params.font_name) and 1 or 0,
                            has_blood=(typography_params.font_name is not None and "Bold" in typography_params.font_name) and 1 or 0,
                            has_capital_start=(t_text[0].isalpha() and t_text[0].isupper()) and 1 or 0,
                            proportion_capital_letters=round(sum(c.isupper() for c in t_text) / max(1, sum(c.isalpha() for c in t_text)), 2),
                            relative_space_left = round(p_left / page_params.width, 2),
                            # relative_space_rigth= round(p_right / page_params.width, 2),
                            relative_space_top = round(p_top / page_params.height, 2),
                            relative_height=round((p_bottom - p_top) / page_params.height, 3)
                        ),
                    )
                    page_blocks.append(structure_block)


# endregion
# ============================================================
# region Изображения
# ============================================================

    def extract_images_from_page(   
        self,
        page: pymupdf.Page,
        page_blocks: List[DocumentBlock],
        page_params: PageParameters,
    ):
        images = page.get_images(full=True)
        for img_idx, img in enumerate(images):
            try:
                xref = img[0]
                base_image = self.doc.extract_image(xref)

                image_rects = page.get_image_rects(xref)

                # output_dir = "extracted_images"
                # os.makedirs(output_dir, exist_ok=True)
                # image_filename = (
                #     f"page_{page_params.number + 1}_img_{img_idx}.{base_image['ext']}"
                # )
                # image_path = os.path.join(output_dir, image_filename)

                # with open(image_path, "wb") as f:
                #     f.write(base_image["image"])

                block = DocumentBlock(
                    parsed_type=BlockParsedType.IMAGE,
                    parsed_data=ParsedBlockData(
                        data=ImageBlockData(
                            width=base_image["width"],
                            height=base_image["height"],
                            ext=base_image["ext"],
                            saved_path="image_path",
                        ),
                        geometry=BlockGeometry(
                            left=int(image_rects[0].x0),
                            right=int(image_rects[0].x1),
                            top=int(image_rects[0].y0),
                            bottom=int(image_rects[0].y1),
                        ),
                        page_parameters=page_params
                    ),
                    normalized_data=NormalizeTextBlockData()
                )

                page_blocks.append(block)

            except Exception as e:
                print(f"[ERROR] - Ошибка парсинга изображения: {e}")
                continue
        
# endregion
# ============================================================
# region Таблицы
# ============================================================

    
    def extract_tables_from_page(
        self,
        page: pymupdf.Page,
        page_blocks: List[DocumentBlock],
        page_params: PageParameters,
    ):
        tabs = page.find_tables()
        if not tabs or not tabs.tables:
            return

        assigned_block_ids: set[int] = set()

        for tab in tabs.tables:
            try:
                table_data = tab.extract()
                if not table_data:
                    continue

                n_rows = len(table_data)
                n_cols = max(len(r) for r in table_data)
                t_x0, t_y0, t_x1, t_y1 = tab.bbox

                # 1. Группируем логические позиции по физическим bbox (merged cells)
                from collections import defaultdict
                bbox_to_positions: dict[tuple[float, float, float, float], list[tuple[int, int]]] = defaultdict(list)

                for r_idx, row in enumerate(table_data):
                    for c_idx, _ in enumerate(row):
                        exp_w = (t_x1 - t_x0) / n_cols
                        exp_h = (t_y1 - t_y0) / n_rows
                        ex0 = t_x0 + c_idx * exp_w
                        ey0 = t_y0 + r_idx * exp_h

                        best_bbox: Optional[tuple[float, float, float, float]] = None
                        best_overlap = 0.0

                        for phys in tab.cells:
                            px0, py0, px1, py1 = phys
                            ox = max(0, min(ex0 + exp_w, px1) - max(ex0, px0))
                            oy = max(0, min(ey0 + exp_h, py1) - max(ey0, py0))
                            area = ox * oy
                            if area > best_overlap:
                                best_overlap = area
                                best_bbox = phys

                        if best_bbox:
                            bbox_to_positions[tuple(best_bbox)].append((r_idx, c_idx))

                # 2. Создаем ячейки с НОВЫМИ блоками
                cells: List[TableCell] = []

                for bbox_tuple, positions in bbox_to_positions.items():
                    rows = [p[0] for p in positions]
                    cols = [p[1] for p in positions]
                    
                    first_r, first_c = positions[0]
                    cell_text = ""
                    if first_r < len(table_data) and first_c < len(table_data[first_r]):
                        val = table_data[first_r][first_c]
                        cell_text = str(val).strip() if val else ""

                    # ДОБЫВАЕМ ТИПОГРАФИКУ ПРЯМО ИЗ СТРАНИЦЫ ПО КООРДИНАТАМ ЯЧЕЙКИ
                    typography = None
                    try:
                        clip = pymupdf.Rect(bbox_tuple)
                        # Получаем текстовые фрагменты внутри этой области
                        blocks_dict = page.get_text("dict", clip=clip, flags=pymupdf.TEXT_PRESERVE_WHITESPACE)["blocks"]
                        
                        fonts = []
                        sizes = []
                        colors = []
                        
                        for b in blocks_dict:
                            for l in b.get("lines", []):
                                for s in l.get("spans", []):
                                    if s.get("text", "").strip():
                                        fonts.append(s.get("font", ""))
                                        sizes.append(s.get("size", 0))
                                        # Цвет в PyMuPDF часто в формате (r,g,b) или hex
                                        c = s.get("color", 0)
                                        if isinstance(c, int):
                                            colors.append(f"#{c:06X}")
                                        else:
                                            colors.append(str(c))

                        if fonts:
                            # Берем самый частый шрифт/размер в ячейке
                            from collections import Counter
                            main_font = Counter(fonts).most_common(1)[0][0]
                            main_size = Counter(sizes).most_common(1)[0][0]
                            main_color = Counter(colors).most_common(1)[0][0] if colors else "#000000"
                            
                            typography = TextTypography(
                                font_name=main_font,
                                font_size=round(main_size, 1),
                                color=main_color
                            )
                    except Exception:
                        pass  # Если не удалось добыть типографику, оставляем None

                    # СОЗДАЕМ НОВЫЙ БЛОК С ГАРАНТИРОВАННЫМ ТЕКСТОМ И ТИПОГРАФИКОЙ
                    new_block = DocumentBlock(
                        parsed_type=BlockParsedType.TEXT,
                        parsed_data=ParsedBlockData(
                            data=TextBlockData(text=cell_text, typography=typography),
                            geometry=BlockGeometry(
                                left=bbox_tuple[0], top=bbox_tuple[1],
                                right=bbox_tuple[2], bottom=bbox_tuple[3]
                            ),
                            page_parameters=page_params,
                        ),
                        normalized_data=NormalizeTextBlockData()
                    )

                    tc = TableCell(
                        row=(min(rows), max(rows)),
                        col=(min(cols), max(cols)),
                        geometry=BlockGeometry(
                            left=bbox_tuple[0], top=bbox_tuple[1],
                            right=bbox_tuple[2], bottom=bbox_tuple[3]
                        ),
                        text_blocks=[new_block]
                    )
                    cells.append(tc)

                # 3. Формируем блок таблицы
                table_block = DocumentBlock(
                    parsed_type=BlockParsedType.TABLE,
                    parsed_data=ParsedBlockData(
                        data=TableBlockData(cells=cells),
                        geometry=BlockGeometry(
                            left=int(t_x0), top=int(t_y0),
                            right=int(t_x1), bottom=int(t_y1)
                        ),
                        page_parameters=page_params,
                    ),
                    normalized_data=NormalizeTextBlockData()
                )

                # 4. Мутация списка
                page_blocks.append(table_block)
                
                # Удаляем из page_blocks только те блоки, которые ТОЧНО попали внутрь таблицы
                # (если они там вообще остались после find_tables)
                page_blocks[:] = [
                    b for b in page_blocks
                    if b is table_block or 
                    not (_point_in_bbox((b.parsed_data.geometry.left + b.parsed_data.geometry.right)/2,
                                        (b.parsed_data.geometry.top + b.parsed_data.geometry.bottom)/2,
                                        [t_x0, t_y0, t_x1, t_y1]))
                ]

            except Exception as e:
                print(f"[ERROR] Ошибка парсинга таблицы на стр. {page_params.number}: {e}")
                import traceback
                traceback.print_exc()
                continue

def _get_hex(colorInt: int) -> str:
    r = (colorInt >> 16) & 255
    g = (colorInt >> 8) & 255
    b = colorInt & 255
    return(f"#{r:02x}{g:02x}{b:02x}")

def _point_in_bbox(x: float, y: float, bbox: List[float]) -> bool:
    """Проверяет, попадает ли точка (x, y) внутрь bbox."""
    return bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]


