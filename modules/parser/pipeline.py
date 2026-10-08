import sys
from pathlib import Path
from typing import Any, Dict, List

PARSER_DIR = Path(__file__).resolve().parent
if str(PARSER_DIR) not in sys.path:
    sys.path.insert(0, str(PARSER_DIR))

try:
    from .parsers.docx_parser import DocxParser
    from .parsers.pdf_parser_new import PdfParser
except ImportError:  # pragma: no cover - fallback for direct execution
    from parsers.docx_parser import DocxParser
    from parsers.pdf_parser_new import PdfParser

def get_parser(file_path: str | Path):
    file_path = Path(file_path)
    extension = file_path.suffix.lower()

    if extension == ".docx":
        return DocxParser()
    elif extension == ".pdf":
        return PdfParser()
    else:
        raise ValueError(f"Формат файла {extension} не поддерживается")
