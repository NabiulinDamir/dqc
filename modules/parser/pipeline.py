import sys
from pathlib import Path
from typing import Any, Dict, List

PARSER_DIR = Path(__file__).resolve().parent
if str(PARSER_DIR) not in sys.path:
    sys.path.insert(0, str(PARSER_DIR))

try:
    from .parsers.docx_parser import DocxParser
    from .parsers.pdf_parser import PdfParser
except ImportError:  # pragma: no cover - fallback for direct execution
    from parsers.docx_parser import DocxParser
    from parsers.pdf_parser import PdfParser


def _normalize_block(block: Any) -> Dict[str, Any]:
    if hasattr(block, "to_dict"):
        return dict(block.to_dict())
    if isinstance(block, dict):
        return dict(block)
    return {"content": str(block), "type": "unknown"}


def parse_document(file_path: str | Path) -> List[Any]:
    file_path = Path(file_path)
    extension = file_path.suffix.lower()

    # if extension == ".docx":
    #     blocks = DocxParser().parse(str(file_path))
    if extension == ".pdf":
        parsed_document = PdfParser().parse(str(file_path))
    else:
        raise ValueError(f"Формат файла {extension} не поддерживается")

    # if isinstance(blocks, list) and blocks and isinstance(blocks[0], dict) and isinstance(blocks[0].get("blocks"), list):
    #     return [
    #         {
    #             **page,
    #             "blocks": [_normalize_block(raw_block) for raw_block in page.get("blocks", [])],
    #         }
    #         for page in blocks
    #     ]

    return parsed_document
