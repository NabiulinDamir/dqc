import argparse
import json
import sys
import time
from pathlib import Path
from typing import List
import fitz

import webbrowser
import os

from modules.document import Document, CustomEncoder, DocumentBlock

# Настройка путей проекта
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.parser.pipeline import get_parser
from modules.classification.pipeline import get_classifier
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
        default=str(PROJECT_ROOT / "data/input" / "дипломпдф.pdf"),
        help="Путь к документу",
    )
    parser.add_argument(
        "--parser_output",
        default=str(PROJECT_ROOT / "data/output" / "parser_result.json"),
        help="Путь для сохранения результата парсера",
    )
    parser.add_argument(
        "--classification_output",
        default=str(PROJECT_ROOT / "data/output" / "classification_result.json"),
        help="Путь для сохранения результата классификации",
    )
    parser.add_argument(
        "--marked_output",
        default=str(PROJECT_ROOT / "data/output" / "marked_result.pdf"),
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
    parser.add_argument(
        '--train',
        action='store_true',
        help='Запустить только обучение модели'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Протестировать модель после обучения'
    )
    parser.add_argument(
        '--classify',
        action='store_true',
        help='Запустить только классификацию'
    )
    parser.add_argument(
        '--parse',
        action='store_true',
        help='Запустить только парсинг'
    )


    args = parser.parse_args()

    if args.train:
        train_ml_classifer("data/train") 
        return

    if args.test:
        test_ml_classifer("data/test")
        return

    if(not args.classify and not args.parse):
        train_ml_classifer("data/train") 
        test_ml_classifer("data/test")

    input_path = Path(args.file_path)
    if not input_path.is_absolute():
        input_path = (PROJECT_ROOT / input_path).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Файл не найден: {input_path}")

    start_time = time.time()
    print("[TIMING] Начало обработки ------------------------------------------------------")

    new_document: Document = Document(input_path)
    
    if(args.parse_result == 'new'):
        new_document.parse(get_parser(input_path))
    else:
        new_document.blocks = json.load(open(args.parser_output, 'r', encoding='utf-8')).get("blocks", [])

    save_json(Path(args.parser_output), new_document)
    print(f"[TIMING] Парсинг завершен: {time.time() - start_time:.2f} с")

    if args.parse: return

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


def train_ml_classifer(folder: str):
    # Распарсить каждый документ и сложить блоки
    print("[INFO] Начало обучения ------------------------------------------------------")
    start_time = time.time()

    all_blocks = get_blocks_from_folder(folder + "/marked")

    marker_classifer = get_classifier("marker")
    classify_data = marker_classifer.classify(all_blocks)

    save_json(Path("data/output/train_blocks_classiffy.json"), classify_data)

    ml_classifer = get_classifier("ml")
    ml_classifer.train(classify_data)

    print(f"[TIMING] Общее время выполнения: {time.time() - start_time:.2f} с")
    print("[INFO] Конец обучения ------------------------------------------------------")
    return

def test_ml_classifer(folder: str):
    print("[INFO] Начало тестирования ------------------------------------------------------")
    all_blocks = get_blocks_from_folder(folder)
    marker_classifer = get_classifier("marker")
    classify_data = marker_classifer.classify(all_blocks)
    ml_classifer = get_classifier("ml")
    ml_classifer.test(all_blocks)
    print("[INFO] Конец тестирования -------------------------------------------------------")
    

def get_blocks_from_folder(path: str):
    all_blocks: List[DocumentBlock] = []
    folder_marker = Path(path)
    pdf_files = list(folder_marker.glob("*.pdf"))
    for file in pdf_files:
        print(file)
        all_blocks.extend(get_blocks_from_document(file))
    return all_blocks

def get_blocks_from_document(path: str):
    new_document = Document(path)
    new_document.parse(get_parser(path))
    return new_document.blocks

if __name__ == "__main__":
    main()
