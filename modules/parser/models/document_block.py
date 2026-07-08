from dataclasses import dataclass
from enum import Enum
from typing import Optional, List

class BlockType(Enum):
    TEXT = "text"           # Обычный параграф
    # HEADING = "heading"     # Заголовок (нужен уровень 1-9)
    LIST_ITEM = "list_item" # Элемент списка
    TABLE = "table" # Строка таблицы (упрощенно)
    IMAGE = "image" # Подпись к рисунку/таблице
    UNKNOWN = "unknown"
    
@dataclass
class DocumentBlock:
    content: str            # Чистый текст
    type: BlockType   # Тип блока
    id: Optional[str] = None
    # level: Optional[int] = None
    # page_number: int = 0    # Номер страницы (важно для PDF)
    
    
    def __repr__(self):
        prefix = ""
        if self.type == BlockType.TEXT:
            prefix = "[Text]:"
        # elif self.block_type == BlockType.HEADING:
        #     prefix = f"[H{self.level}]: "
        elif self.type == BlockType.LIST_ITEM:
            prefix = f"[LIST]: "
        elif self.type == BlockType.TABLE:
            prefix = "[TABLE]:\n"
        elif self.type == BlockType.IMAGE:
            prefix = "[IMAGE]: "
            
        return f"{prefix}{self.content}"
    
    def to_dict(self):
        return {
            "content": self.content,
            "type": self.type.value,
            "id": self.id,
            # "level": self.level
            # "page_number": self.page_number,
        }
        

        