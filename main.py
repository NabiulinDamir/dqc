import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Импорт основных модулей системы
from modules.parser.pipeline import parse_document
from modules.classification.pipeline import classify_blocks


def save_json(path: Path, data):
    """Сохраняет данные в JSON-файл с созданием папки при необходимости."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def main():
    """Точка входа: парсинг документа, классификация блоков и сохранение результатов."""
    parser = argparse.ArgumentParser(description="Главный запускной файл системы")
    parser.add_argument(
        "file_path",
        nargs="?",
        default=str(PROJECT_ROOT / "docx" / "дипломпдф.pdf"),
        help="Путь к документу (.docx или .pdf)",
    )
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "output" / "result.json"),
        help="Файл для сохранения блоков с классификацией",
    )
    parser.add_argument(
        "--classification-output",
        default=str(PROJECT_ROOT / "output" / "classification_result.json"),
        help="Файл для сохранения блоков с добавленным полем classified_type",
    )
    parser.add_argument(
        "--classification",
        choices=["rule_based", "neural"],
        default="rule_based",
        help="Способ классификации: rule_based или neural",
    )
    args = parser.parse_args()

    input_path = Path(args.file_path)
    if not input_path.is_absolute():
        input_path = (PROJECT_ROOT / input_path).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Файл не найден: {input_path}")

    # 1. Извлечение блоков из документа
    blocks = parse_document(input_path)

    # 2. Классификация блоков выбранным способом
    classified_blocks = classify_blocks(blocks, method=args.classification)

    # 3. Сохранение результатов в JSON
    save_json(Path(args.output), blocks)
    save_json(Path(args.classification_output), classified_blocks)

    print(f"Обработан файл: {input_path}")
    print(f"Получено блоков: {len(blocks)}")
    print(f"Базовые блоки сохранены в: {Path(args.output)}")
    print(f"Блоки с classified_type сохранены в: {Path(args.classification_output)}")
    print(f"Использован метод классификации: {args.classification}")


if __name__ == "__main__":
    main()
