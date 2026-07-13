import argparse
import json
import sys
import time
from pathlib import Path

# Настройка путей проекта
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.parser.pipeline import parse_document
from modules.classification.pipeline import classify_blocks


def save_json(path: Path, data):
    """Вспомогательная функция для сохранения структуры в файл"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def main():
    parser = argparse.ArgumentParser(description="Главный запускной файл системы")
    parser.add_argument(
        "file_path",
        nargs="?",
        default=str(PROJECT_ROOT / "docx" / "дипломпдф.pdf"),
        help="Путь к документу",
    )
    parser.add_argument(
        "--parser_output",
        default=str(PROJECT_ROOT / "output" / "parser_result.json"),
        help="Путь для сохранения результата парсера",
    )
    parser.add_argument(
        "--classification_output",
        default=str(PROJECT_ROOT / "output" / "classification_result.json"),
        help="Путь для сохранения результата классификации",
    )
    parser.add_argument(
        "--classification",
        choices=["rule_based", "neural"],
        default="rule_based",
        help="Способ классификации",
    )
    args = parser.parse_args()

    input_path = Path(args.file_path)
    if not input_path.is_absolute():
        input_path = (PROJECT_ROOT / input_path).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Файл не найден: {input_path}")

    start_time = time.time()
    print(
        "[TIMING] Начало обработки ------------------------------------------------------"
    )

    # 1. Извлечение текста и геометрии (работает ваш PyMuPDF код)
    parsed_document = parse_document(input_path)
    document_blocks = parsed_document.get("blocks", [])
    print(f"[TIMING] Парсинг завершен: {time.time() - start_time:.2f} с")
    
    # 2. Классификация извлеченных блоков (добавление типов)
    # classified_blocks = classify_blocks(document_blocks, method=args.classification)

    print(f"[TIMING] Классификация завершена: {time.time() - start_time:.2f} с")
    # 3. Сохранение финального результата (сразу с классами)
    save_json(Path(args.parser_output), document_blocks)
    # save_json(Path(args.classification_output), classified_blocks)

    print(f"[TIMING] Результат успешно сохранен в: {args.classification_output}")
    print(f"[TIMING] Общее время выполнения: {time.time() - start_time:.2f} с")
    print(
        "[TIMING] Конец обработки ------------------------------------------------------"
    )


if __name__ == "__main__":
    main()
