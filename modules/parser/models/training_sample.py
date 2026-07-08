from dataclasses import dataclass
from enum import Enum
from typing import Optional, List

class BlockType(Enum):
    TEXT = "text"          
    LIST_ITEM = "list_item" 
    UNKNOWN = "unknown"
    TABLE = "table"
    HEADING = "heading"
    TABLE_CAPTION = "tbl_caption"
    IMAGE_CAPTION = "img_caption"
    LISTING_CAPTION = "ltg_caption"
    LISTING = "listing"
    FORMULA = "formula"
    
    LITERATURE_LIST = "literature_list"
    # TITLE_PAGE = "title_page_item"       #раскрыть
    CONTENTS = "contents"
    TERM = "term"
    PLACE_TO_SIGN = "place_to_sign"
    PLACE_TO_DATE = "place_to_date"
    
    

@dataclass
class TrainingSample:
    content: str            # Чистый текст
    type: str               # Тип блока
    level: Optional[int] = None
    # semantic_role: str

    
    def to_dict(self):
        return {
            "content": self.content,
            "type": self.type,
            "level": self.level
        }
        