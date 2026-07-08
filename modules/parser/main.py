import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PARSER_ROOT = PROJECT_ROOT / "modules" / "parser"

if str(PARSER_ROOT) not in sys.path:
    sys.path.insert(0, str(PARSER_ROOT))

from pipeline import parse_document


def main():
    default_file = PROJECT_ROOT / "docx" / "дипломпдф.pdf"
    file_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else default_file

    if not file_path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    blocks = parse_document(file_path)
    print(f"Обработан файл: {file_path}")
    print(f"Получено элементов: {len(blocks)}")


if __name__ == "__main__":
    main()