import argparse
import json
import sys
import time
from pathlib import Path
from typing import List
import fitz

import webbrowser
import os

from modules.document import DocumentBlock, Document
from modules.utils import CustomEncoder

# Настройка путей проекта
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.parser.pipeline import get_parser
from modules.classification.pipeline import get_classifier
from modules.markup.pipeline import get_marker



    
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
        '--train',
        action='store_true',
        help='Запустит обучение модели на всех документах в data/train'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Запустит ntcn модели на всех документах в data/test'
    )
    parser.add_argument(
        '--parse',
        action='store_true',
        help='Распарсит все документы в parser_result.json из data/input '
    )
    parser.add_argument(
        '--classify',
        action='store_true',
        help='Классифицирует ml классификатором данные из classify_result.json'
    )
    parser.add_argument(
        '--mark',
        action='store_true',
        help='Маркирует документы data/input из classify_result.json'
    )


    args = parser.parse_args()
    start_time = time.time()

    if args.train:
        train_ml_classifer("data/train") 

    if args.test:
        test_ml_classifer("data/test")

    all_documents: List[Document] = get_docs_from_folder("data/input")

    if args.parse:
        parse_all_documents(all_documents, args.parser_output)

    if args.classify:
        classify_all_documents(all_documents, args.classification_output)

    if args.mark:
        mark_all_documents(all_documents, args.marked_output)
        webbrowser.open(f"file:///{os.path.abspath(args.marked_output)}")
        
    print(f"[TIMING] Общее время выполнения: {time.time() - start_time:.2f} с")



def parse_all_documents(all_documents: List[DocumentBlock], save_path: str):
    start_time = time.time()
    print("[INFO] Начало парсинга")
    for document in all_documents:
        document.parse(get_parser(document.path))
    save_json(Path(save_path), all_documents)
    print(f"[TIMING] Парсинг завершен за {time.time() - start_time:.2f} с")


def classify_all_documents(all_documents: List[DocumentBlock], save_path: str):
    start_time = time.time()
    print("[INFO] Начало классификации")
    for document in all_documents:
        document.classify(get_classifier("ml"))
    save_json(Path(save_path), all_documents)
    print(f"[TIMING] Классификация завершена за {time.time() - start_time:.2f} с")


def mark_all_documents(all_documents: List[DocumentBlock], save_path: str):
    start_time = time.time()
    print("[INFO] Начало маркировки")
    for document in all_documents:
        document.markup(marker= get_marker(), output_path= save_path)
    print(f"[TIMING] Маркировка завершена за {time.time() - start_time:.2f} с")



def train_ml_classifer(folder: str):
    start_time = time.time()
    print("[INFO] Начало обучения")
    start_time = time.time()
    all_documents = get_docs_from_folder(folder + "/marked")
    marker_classifer = get_classifier("marker")
    ml_classifer = get_classifier("ml")

    for document in all_documents:
        document.parse(get_parser(document.path))
        document.classify(marker_classifer)

    docs_blocks: List[List[DocumentBlock]] = [document.blocks for document in all_documents]
    save_json(Path("data/output/train_blocks_classiffy.json"), docs_blocks)
    ml_classifer.train(docs_blocks)

    print(f"[TIMING] Обучение завершено за {time.time() - start_time:.2f} с")

def test_ml_classifer(folder: str):
    start_time = time.time()
    print("[INFO] Начало тестирования")
    all_documents = get_docs_from_folder(folder)
    marker_classifer = get_classifier("marker")
    ml_classifer = get_classifier("ml")
    for document in all_documents:
        document.parse(get_parser(document.path))
        document.classify(marker_classifer)
    
    docs_blocks: List[List[DocumentBlock]] = [document.blocks for document in all_documents]
    ml_classifer.test(docs_blocks)

    print(f"[TIMING] Тестирование завершено за {time.time() - start_time:.2f} с")
    

def get_docs_from_folder(path: str) -> List[Document]:
    result: List[Document] = []
    folder_marker = Path(path)
    pdf_files = list(folder_marker.glob("*.pdf"))
    if(len(pdf_files) < 1): print("[WARN] Дирректория input пустая")
    for file in pdf_files:
        new_document = Document(file)
        result.append(new_document)
    return result


def save_json(path: str | Path, data):
    target_path = Path(path)
    # Создаем папку, если её нет (например, data/output/)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    with target_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4, cls=CustomEncoder)


if __name__ == "__main__":
    main()
