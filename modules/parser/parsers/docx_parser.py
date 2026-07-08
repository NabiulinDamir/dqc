import docx
import json
import re
from docx.oxml.ns import qn
from typing import List
from models.document_block import DocumentBlock, BlockType
from models.training_sample import TrainingSample, BlockType as TraningBlockType
from models.patterns import LIST_PATTERNS

class DocxParser():
    def parse(self, file_path: str) -> List[DocumentBlock]:
        doc = docx.Document(file_path)
        blocks = []

        table_index = 0
        toc_index = 0
        image_index = 0 

        # Итерируемся по телу документа в порядке их реального расположения
        for element in doc.element.body:
            tag_name = element.tag.split('}')[-1]

            # -------------------------------------------------Параграф-----------------------------------------
            if tag_name == 'p':
                if element.xpath('./ancestor::*[local-name()="sdt"]'):
                    continue

                # Находим объект параграфа в python-docx по совпадению элемента
                para = next((p for p in doc.paragraphs if p._element == element), None)
                if not para:
                    continue

                # -------------------------------------------------Изображения-----------------------------------------
                # Ищем тег <w:blip>, который содержит ссылку (embed rId) на файл изображения
                blip_elements = element.xpath('.//*[local-name()="blip"]')
                
                if blip_elements:
                    for blip in blip_elements:
                        # Достаем атрибут связи rId (обычно это w:embed или r:embed)
                        rId = None
                        for attr_name, attr_value in blip.attrib.items():
                            if attr_name.endswith('embed'):
                                rId = attr_value
                                break
                        
                        if rId and rId in doc.part.related_parts:
                            img_part = doc.part.related_parts[rId]
                            filename = img_part.filename
                            
                            blocks.append(DocumentBlock(
                                content=f"Image: {filename}",
                                type=BlockType.IMAGE,
                                id= f"img_{image_index}",
                            ))
                            image_index += 1
                    
                    # Проверяем, есть ли в этом параграфе еще и обычный текст помимо картинки.
                    # Если текста нет (чистый параграф-контейнер для фото), переходим к следующему блоку.
                    if not para.text.strip():
                        continue

                # -------------------------------------------------Текст-----------------------------------------
                text = para.text.strip()
                if not text:
                    continue

                type_block = BlockType.TEXT
                para_id = para._element.get(qn('w14:paraId'))

                # -------------------------------------------------Список-----------------------------------------
                if para._element.xpath('./w:pPr/w:numPr'):  
                    type_block = BlockType.LIST_ITEM
                    val_attr = para._element.xpath('./w:pPr/w:numPr/w:ilvl/@w:val')
                    list_level = int(val_attr[0]) if val_attr else 0
                    
                    markers = ["•", "*", "+", "-"]
                    marker = markers[list_level] if list_level < len(markers) else "•"
                    text = f"{marker} {text}"

                blocks.append(DocumentBlock(
                    content=text,
                    type=type_block,
                    id= f"par_{para_id}"
                ))

            # -------------------------------------------------Таблицы--------------------------------------------
            elif tag_name == 'tbl':
                if element.xpath('./ancestor::*[local-name()="sdt"]'):
                    continue

                table = next((t for t in doc.tables if t._element == element), None)
                if table:
                    table_rows = []
                    for row in table.rows:
                        row_text = " | ".join(cell.text.strip() for cell in row.cells)
                        if row_text.strip():
                            table_rows.append(row_text)
                    
                    if table_rows:
                        blocks.append(DocumentBlock(
                            content="\n".join(table_rows),
                            type=BlockType.TABLE,
                            id= f"tbl_{table_index}"
                        ))
                        table_index += 1
                        
            # -------------------------------------------------Оглавление-----------------------------------------
            elif tag_name == 'sdt':
                is_toc = bool(element.xpath('.//*[local-name()="hyperlink"] or .//*[local-name()="fldSimple"][contains(@*[local-name()="instr"], "TOC")]'))
                if is_toc:
                    toc_rows = []
                    for p in element.xpath('.//*[local-name()="p"]'):
                        text_nodes = p.xpath('.//*[local-name()="r"]/*[local-name()="t"]')
                        p_text = "".join([node.text for node in text_nodes if node.text]).strip()
                        if p_text:
                            toc_rows.append(p_text)
                    
                    if toc_rows:
                        blocks.append(DocumentBlock(
                            content="\n".join(toc_rows),
                            type=BlockType.TABLE,  
                            id=f"toc_{toc_index}"
                        ))
                        toc_index += 1
                    continue 

        # Сохранение в JSON
        # blocks_json = [block.to_dict() for block in blocks]
        # with open("result_parser.json", "w", encoding="utf-8") as f:
        #     json.dump(blocks_json, f, ensure_ascii=False, indent=4)
        
        return blocks


        
        
    def parseTraningSample(self, file_path: str) -> List[TrainingSample]:
        doc = docx.Document(file_path)
        blocks = []

        for element in doc.element.body:
            tag_name = element.tag.split('}')[-1]

            # -------------------------------------------------Параграф-----------------------------------------
            if tag_name == 'p':
                if element.xpath('./ancestor::*[local-name()="sdt"]'):
                    continue

                # Находим объект параграфа в python-docx по совпадению элемента
                para = next((p for p in doc.paragraphs if p._element == element), None)
                if not para:
                    continue

                # -------------------------------------------------Изображения-----------------------------------------
                

                # -------------------------------------------------Текст-----------------------------------------
                text = para.text.strip()
                if not text:
                    continue

                type_block = BlockType.TEXT
                para_id = para._element.get(qn('w14:paraId'))

                # -------------------------------------------------Список-----------------------------------------
                if para._element.xpath('./w:pPr/w:numPr'):  
                    type_block = BlockType.LIST_ITEM
                    val_attr = para._element.xpath('./w:pPr/w:numPr/w:ilvl/@w:val')
                    list_level = int(val_attr[0]) if val_attr else 0
                    
                    markers = ["•", "*", "+", "-"]
                    marker = markers[list_level] if list_level < len(markers) else "•"
                    text = f"{marker} {text}"

                blocks.append(DocumentBlock(
                    content=text,
                    type=type_block,
                    id= f"par_{para_id}"
                ))

            # -------------------------------------------------Таблицы--------------------------------------------
            elif tag_name == 'tbl':
                if element.xpath('./ancestor::*[local-name()="sdt"]'):
                    continue

                table = next((t for t in doc.tables if t._element == element), None)
                if table:
                    table_rows = []
                    for row in table.rows:
                        row_text = " | ".join(cell.text.strip() for cell in row.cells)
                        if row_text.strip():
                            table_rows.append(row_text)
                    
                    if table_rows:
                        blocks.append(DocumentBlock(
                            content="\n".join(table_rows),
                            type=BlockType.TABLE,
                            id= f"tbl_{table_index}"
                        ))
                        table_index += 1
                        
            # -------------------------------------------------Оглавление-----------------------------------------
            elif tag_name == 'sdt':
                is_toc = bool(element.xpath('.//*[local-name()="hyperlink"] or .//*[local-name()="fldSimple"][contains(@*[local-name()="instr"], "TOC")]'))
                if is_toc:
                    toc_rows = []
                    for p in element.xpath('.//*[local-name()="p"]'):
                        text_nodes = p.xpath('.//*[local-name()="r"]/*[local-name()="t"]')
                        p_text = "".join([node.text for node in text_nodes if node.text]).strip()
                        if p_text:
                            toc_rows.append(p_text)
                    
                    if toc_rows:
                        blocks.append(DocumentBlock(
                            content="\n".join(toc_rows),
                            type=BlockType.TABLE,  
                            id=f"toc_{toc_index}"
                        ))
                        toc_index += 1
                    continue 

        # Сохранение в JSON
        # blocks_json = [block.to_dict() for block in blocks]
        # with open("result_parser.json", "w", encoding="utf-8") as f:
        #     json.dump(blocks_json, f, ensure_ascii=False, indent=4)
        
        return blocks




    # def checkTextType(text: str) -> TraningBlockType:
        