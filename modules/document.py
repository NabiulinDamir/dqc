from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import numpy as np


# ============================================================
# region Классы
# ============================================================

from enum import Enum
from typing import Dict, Optional


class BlockClassifiedType(Enum):
    UNKNOWN             = "unknown"
    TEXT                = "text"
    HEADING             = "heading"
    NUMBER_LIST_ITEM    = "number_list_item"
    MARKER_LIST_ITEM    = "marker_list_item"
    TABLE_CAPTION       = "table_caption"
    IMAGE_CAPTION       = "image_caption"
    FORMULA             = "formula"
    FOOTER              = "footer"
    CONTENT_ITEM        = "content_item"
    LISTING             = "listing"
    LISTING_CAPTION     = "listing_caption"
    LITERATURE_ITEM     = "literature_item"

    @staticmethod
    def index(enum_value) -> int:
        if isinstance(enum_value, BlockClassifiedType):
            return list(BlockClassifiedType).index(enum_value)
        elif isinstance(enum_value, str):
            return list(BlockClassifiedType).index(BlockClassifiedType(enum_value))
        return 0

    @staticmethod
    def get_color(enum_value) -> Optional[str]:
        if isinstance(enum_value, BlockClassifiedType):
            return _CLASS_TO_COLORS.get(enum_value)
        if isinstance(enum_value, str):
            try:
                return _CLASS_TO_COLORS.get(BlockClassifiedType(enum_value))
            except ValueError:
                return None
        return None

    @staticmethod
    def get_by_color(color: str) -> Optional["BlockClassifiedType"]:
        return _COLORS_TO_CLASS.get(color)

_COLORS_TO_CLASS: Dict[str, BlockClassifiedType] = {
    "#1F3864": BlockClassifiedType.HEADING,
    "#46FF3F": BlockClassifiedType.FOOTER,
    "#21D6DF": BlockClassifiedType.FORMULA,
    "#EE0000": BlockClassifiedType.MARKER_LIST_ITEM,
    "#FFC000": BlockClassifiedType.NUMBER_LIST_ITEM,
    "#ED7D31": BlockClassifiedType.IMAGE_CAPTION,
    "#7030A0": BlockClassifiedType.TABLE_CAPTION,
    "#000000": BlockClassifiedType.TEXT,
    "#106616": BlockClassifiedType.CONTENT_ITEM,
    "#DF21BB": BlockClassifiedType.LISTING,
    "#8D4294": BlockClassifiedType.LISTING_CAPTION,
    "#0070C0": BlockClassifiedType.LITERATURE_ITEM,
}

_CLASS_TO_COLORS: Dict[BlockClassifiedType, str] = {
    cls: color for color, cls in _COLORS_TO_CLASS.items()
}
    
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
    left: Optional[float]    = None  # Координата X (например, левый верхний угол)
    top: Optional[float]     = None  # Координата Y (например, левый верхний угол)
    right: Optional[float]   = None  # Координата X (например, правый нижний угол)
    bottom: Optional[float]  = None  # Координата Y (например,

@dataclass
class PageParameters:
    number: Optional[int]       = None  # Номер страницы
    width: Optional[float]   = None  # Ширина страницы
    height: Optional[float]  = None  # Высота страницы

@dataclass
class TextBlockData:
    # Текст
    text: Optional[str]         = None # Текст блока

@dataclass
class ImageBlockData:  
    # Картинки
    saved_path: Optional[str]   = None  # Путь к сохраненной картинке
    width: Optional[float]   = None  # Ширина картинки
    height: Optional[float]  = None  # Высота картинки
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
    # text_vector: Optional[np.ndarray]                  = None  # Текстовый вектор
    has_capital_start: Optional[int]                   = None  # !Начинается ли с заглавной буквы
    proportion_capital_letters: Optional[float]        = None  # !Доля заглавных букв в тексте
    # Типографические      
    has_italic: Optional[int]                          = None  # !Наличие курсива
    has_blood: Optional[int]                           = None  # !Наличие жирного начертания
    relative_font_size: Optional[float]                = None  # !Размер шрифта относительно других блоков
    relative_margin_top: Optional[float]               = None  # Относительный отступ снизу до сл. строки
    relative_margin_bottom: Optional[float]            = None  # Относительный отступ сверху до пр. строки
    # Геометрические       
    relative_space_left: Optional[float]               = None  # !Относительный отступ слева 0.5 - середина страницы
    relative_space_top: Optional[float]                = None  # !Позиция относительно страницы 0.5 - середина
    relative_height: Optional[float]                   = None  # !Высота относительно страницы ---
    position_in_line: Optional[int]                    = None  # !Позиция в строке
    position_in_page: Optional[int]                    = None  # !Позиция строки в документе
    # Контекстные      
    prev_block_style_similarity: Optional[float]       = None  # Относительная схожесть с предыдущим блоком по стилевым параметрам
    prev_block_classified_type: Optional[int]          = None  # !Классифицированный тип предыдущего блока (2 - заголовок)
    prev_block_parsed_type: Optional[int]              = None  # !Реальный тип предыдущего блока (2 - картинка)
    next_block_parsed_type: Optional[int]              = None  # !Реальный тип следующего блока (2 - картинка)
    # prev_block_text_vector: Optional[np.ndarray]       = None  # Вектор текста предыдущего блока

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
    parsed_data: Optional[ParsedBlockData]                  = None # Данные для проверки на соответствие правилам
    normalized_data: Optional[NormalizeTextBlockData]       = None # Данные для классификации текста

class Document:
    name: Optional[str]         = None
    path: Optional[str]         = None  # Путь к файлу документа (если известен)
    blocks: List[DocumentBlock] = []    # Список блоков документа

    def __init__(self, path: str | Path):  # Принимаем оба типа
        path_obj = Path(path)
        self.name = path_obj.stem
        self.path = str(path_obj)
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
