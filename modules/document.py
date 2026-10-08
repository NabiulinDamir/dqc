from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import numpy as np


# ============================================================
# region Классы
# ============================================================

class BlockClassifiedType(Enum):
    UNKNOWN             = "unknown"
    TEXT                = "text"
    HEADING             = "heading"
    NUMBER_LIST_ITEM    = "number_list_item"
    MARKER_LIST_ITEM    = "marker_list_item"
    # TABLE               = "table"
    TABLE_CAPTION       = "table_caption"
    # IMAGE               = "image"
    IMAGE_CAPTION       = "image_caption"
    FORMULA             = "formula"
    FOOTER              = "footer"

class BlockParsedType(Enum):
    UNKNOWN     = "unknown"
    TEXT        = "text"  # Обычный параграф
    TABLE       = "table"  # Строка таблицы (упрощенно)
    IMAGE       = "image"  # Подпись к рисунку/таблице

@dataclass
class BlockTypography:
    font_name: Optional[str]    = None  # Название шрифта
    font_size: Optional[float]  = None  # Размер шрифта
    color: Optional[str]        = None  # Цвет текста (например, в формате HEX)

@dataclass
class BlockGeometry:
    left_mm: Optional[float]    = None  # Координата X (например, левый верхний угол)
    top_mm: Optional[float]     = None  # Координата Y (например, левый верхний угол)
    right_mm: Optional[float]   = None  # Координата X (например, правый нижний угол)
    bottom_mm: Optional[float]  = None  # Координата Y (например,

@dataclass
class PageParameters:
    number: Optional[int]       = None  # Номер страницы
    width_mm: Optional[float]   = None  # Ширина страницы
    height_mm: Optional[float]  = None  # Высота страницы

@dataclass
class TextBlockData:
    # Текст
    text: Optional[str]         = None # Текст блока

@dataclass
class ImageBlockData:  
    # Картинки
    saved_path: Optional[str]   = None  # Путь к сохраненной картинке
    width_mm: Optional[float]   = None  # Ширина картинки
    height_mm: Optional[float]  = None  # Высота картинки
    ext: Optional[str] = None

@dataclass
class ParsedBlockData: 
    data: Optional[TextBlockData | ImageBlockData]  = None  # Данные блока
    typography: Optional[BlockTypography]           = None # Типографические параметры
    geometry: Optional[BlockGeometry]               = None # Геометрические параметры
    page_parameters: Optional[PageParameters]       = None # Данные страницы

@dataclass
class NormalizeTextBlockData:
    # Тектовые
    text_vector: Optional[np.ndarray]                  = None  # Текстовый вектор
    has_capital_start: Optional[int]                   = None  # !Начинается ли с заглавной буквы
    # Типографические      
    has_italic: Optional[int]                          = None  # !Наличие курсива
    has_blood: Optional[int]                           = None  # !Наличие жирного начертания
    relative_font_size: Optional[float]                = None  # Размер шрифта относительно других блоков
    relative_margin_top: Optional[float]               = None  # Относительный отступ снизу
    relative_margin_bottom: Optional[float]            = None  # Относительный отступ сверху
    # Геометрические       
    relative_space_left: Optional[float]               = None  # Относительный отступ слева
    relative_height: Optional[float]                   = None  # Относительная высота
    position_in_line: Optional[int]                    = None  # !Позиция в строке
    # Контекстные      
    prev_block_style_similarity: Optional[float]       = None  # Относительная схожесть с предыдущим блоком по стилевым параметрам
    prev_block_classified_type: Optional[int]          = None  # Классифицированный тип предыдущего блока (2 - заголовок)
    prev_block_parsed_type: Optional[int]              = None  # !Реальный тип предыдущего блока (2 - картинка)
    next_block_parsed_type: Optional[int]              = None  # !Реальный тип следующего блока (2 - картинка)
    prev_block_text_vector: Optional[np.ndarray]       = None  # Вектор текста предыдущего блока

    def to_vector(self) -> np.ndarray:
        from dataclasses import fields
        scalars = [
            getattr(self, f.name) if getattr(self, f.name) is not None else 0.0
            for f in fields(self)
            if 'vector' not in f.name
        ]
        vectors = [
            np.array(getattr(self, f.name))
            for f in fields(self)
            if 'vector' in f.name and getattr(self, f.name) is not None
        ]
        return np.concatenate([scalars] + vectors) if vectors else np.array(scalars)

@dataclass
class DocumentBlock:
    id: Optional[int]                                       = None
    # error: Optional[BlockError] = None
    classified_type: Optional[BlockClassifiedType]          = None # Классифицированный тип блока
    parsed_type: Optional[BlockParsedType]                  = None # Реальный тип блока
    parsed_data: Optional[ParsedBlockData]            = None # Данные для проверки на соответствие правилам
    normalized_data: Optional[NormalizeTextBlockData] = None # Данные для классификации текста

class Document:
    name: Optional[str]         = None
    path: Optional[str]         = None  # Путь к файлу документа (если известен)
    blocks: List[DocumentBlock] = []    # Список блоков документа

    def __init__(self, path: str):
        self.name = Path(path).stem
        self.path = str(path)
        self.blocks = []

    def parse(self, parser):
        self.blocks = parser.parse(self.path) 

    def classify(self, classifier):
        classifier.classify(self.blocks)

    def markup(self, marker, output_path: str):
        # Здесь можно реализовать логику разметки документа на основе self.blocks
        pass


import inspect

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, np.ndarray):
            return obj.tolist()  
        elif isinstance(obj, np.generic):
            return obj.item()   
        elif inspect.isclass(obj):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith('__')}
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)
