import sys
from pathlib import Path
from typing import List, Any

PARSER_DIR = Path(__file__).resolve().parent
if str(PARSER_DIR) not in sys.path:
    sys.path.insert(0, str(PARSER_DIR))

try:
    from .parsers.docx_parser import DocxParser
    from .parsers.pdf_parser import PdfParser
except ImportError:  # pragma: no cover - fallback for direct execution
    from parsers.docx_parser import DocxParser
    from parsers.pdf_parser import PdfParser


def parse_document(file_path: str | Path) -> List[Any]:
    """Черный ящик парсера: на вход — документ, на выход — список блоков."""
    file_path = Path(file_path)
    extension = file_path.suffix.lower()

    if extension == ".docx":
        parser = DocxParser()
        blocks = parser.parse(str(file_path))
    elif extension == ".pdf":
        parser = PdfParser()
        blocks = parser.parse(str(file_path))
    else:
        raise ValueError(f"Формат файла {extension} не поддерживается")

    if isinstance(blocks, list) and blocks and hasattr(blocks[0], "to_dict"):
        return [block.to_dict() for block in blocks]
    return blocks
