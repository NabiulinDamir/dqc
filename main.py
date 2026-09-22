import argparse
import json
import sys
import time
from pathlib import Path
import fitz

import webbrowser
import os

from modules.document import Document, CustomEncoder

# Настройка путей проекта
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.parser.pipeline import get_parser
from modules.classification.pipeline import classify_blocks, train_ml_classifer, get_classifier
from modules.markup.pipeline import markup_document
from modules.markup.converter import blocks_to_markup

def save_json(path: Path, data):
    """Вспомогательная функция для сохранения структуры в файл"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4, cls=CustomEncoder)

def main():
    parser = argparse.ArgumentParser(description="Главный запускной файл системы")
    parser.add_argument(
        "file_path",
        nargs="?",
        default=str(PROJECT_ROOT / "docx" / "дипломпдф(разметка).pdf"),
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
        "--marked_output",
        default=str(PROJECT_ROOT / "output" / "marked_result.pdf"),
        help="Путь для сохранения результата разметки",
    )
    parser.add_argument(
        "--classification",
        choices=["rule_based", "ml"],
        default="ml",
        help="Способ классификации",
    )
    parser.add_argument(
        "--parse_result",
        choices=["new", "parsed"],
        default="new",
        help="Результат парсинга: парсить новый или использовать уже существующий",
    )
    args = parser.parse_args()

    input_path = Path(args.file_path)
    if not input_path.is_absolute():
        input_path = (PROJECT_ROOT / input_path).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Файл не найден: {input_path}")

    start_time = time.time()
    print("[TIMING] Начало обработки ------------------------------------------------------")

    # Создание нового документа
    new_document: Document = Document(input_path)

    # save_pdf_to_json(input_path, args.parser_output)
    # 1. Извлечение текста и геометрии
    
    if(args.parse_result == 'new'):
        new_document.parse(get_parser(input_path))
    else:
        new_document.blocks = json.load(open(args.parser_output, 'r', encoding='utf-8')).get("blocks", [])

    save_json(Path(args.parser_output), new_document)
    print(f"[TIMING] Парсинг завершен: {time.time() - start_time:.2f} с")

    # 2. Обучение классификатора (если выбран метод ml)
    # train_ml_classifer(new_document.blocks)
    # print(f"[TIMING] Обучение завершено: {time.time() - start_time:.2f} с")

    # 3. Классификация извлеченных блоков (добавление типов)
    # classified_blocks = classify_blocks(new_document.blocks, method=args.classification)
    new_document.classify(get_classifier(args.classification))
    print(f"[TIMING] Классификация завершена: {time.time() - start_time:.2f} с")
    save_json(Path(args.classification_output), new_document.blocks)

    markup_document(input_path, args.marked_output, blocks_to_markup(new_document.blocks))
    print(f"[TIMING] Маркировка завершена: {time.time() - start_time:.2f} с")

    print(f"[INFO] Результат успешно сохранен в: {args.classification_output}")

    webbrowser.open(f"file://{args.marked_output}")

    print(f"[TIMING] Общее время выполнения: {time.time() - start_time:.2f} с")
    print(
        "[POINT] Конец обработки ------------------------------------------------------"
    )

    


def save_pdf_to_json(pdf_path, output_path):
    doc = fitz.open(pdf_path)

    # Создаем обычный словарь для хранения данных
    pdf_data = {"metadata": doc.metadata, "page_count": doc.page_count, "pages": []}

    # Проходим по каждой странице
    for page in doc:
        page_data = {
            "number": page.number,
            "width": page.rect.width,
            "height": page.rect.height,
            # "dict" возвращает блоки с текстом, шрифтами и координатами (идеально для твоей задачи)
            "text_blocks": page.get_text("dict")["blocks"],
            # Изображения возвращаются кортежами, json их не любит, превращаем в списки
            "images": [list(img) for img in page.get_images()],
        }
        pdf_data["pages"].append(page_data)

    doc.close()  # Обязательно закрываем файл, иначе Windows может его заблокировать

    # Сохраняем обычный словарь в JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pdf_data, f, ensure_ascii=False, indent=4)

    print(f"Данные успешно сохранены в {output_path}")


if __name__ == "__main__":
    main()
