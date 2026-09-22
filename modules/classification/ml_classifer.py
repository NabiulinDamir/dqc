from typing import Any, Dict, List, Optional

from .base import BaseClassifier, ClassificationResult

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
import pymorphy2
from nltk.tokenize import WordPunctTokenizer
from nltk.corpus import stopwords
import re

from ..document import (
    BlockParsedType,
    BlockClassifiedType,
    DocumentBlock,
    ParsedBlockData,
    BlockTypography,
    BlockGeometry,
    PageParameters,
    BlockParsedType,
    NormalizeBlockData,
    TextBlockData
)

# Инициализация инструментов
morph = pymorphy2.MorphAnalyzer()
tokenizer = WordPunctTokenizer()
stop_words = set(stopwords.words('russian'))


def custom_tokenizer(text):
    text = str(text).lower()
    # Немного улучшил паттерн, чтобы он ловил 1.1.1. целиком
    pattern = r"(\d+(?:\.\d+)*[\.)]|[•\-\—\–]|[а-яa-z]{3,})"
    tokens = re.findall(pattern, text)

    result = []
    for token in tokens:
        if token in stop_words:
            continue
        if re.search(r"\d+", token):
            normalized = re.sub(r"\d+", "n", token)
            result.append(normalized)
        elif re.match(r"^[а-яa-z]{3,}$", token):
            lemma = morph.parse(token)[0].normal_form
            result.append(lemma)
        else:
            result.append(token)

    if not result:
        return ["emptyToken"]

    return result

def extracted_block_text(block: DocumentBlock) -> str:
    if block and isinstance(block.parsed_block_data.data, TextBlockData):
        text = block.parsed_block_data.data.text or "emptyText"
    else:
        text = "emptyText"
    return text

class MlClassifier(BaseClassifier):
    """
    Базовый машинно-обучаемый классификатор.
    """

    def __init__(self):
        super().__init__(name="ml")
        self.vectorizer = None
        self.all_vectors = None

    def classify(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        previous_block = None
        current_block = None
        next_block = None

        blocks.append(None)

        path = 'modules/classification/model/tfidf_vectorizer.pkl'
        self.vectorizer = joblib.load(path)
        all_texts = [extracted_block_text(block) for block in blocks]
        self.all_vectors = self.vectorizer.transform(all_texts)

        print("Вектор документа создан")
        print(f"Матрица: {self.all_vectors.shape}")

        print(len(blocks))

        classifed_blocks = []
        for index, block in enumerate(blocks):

            previous_block = current_block
            current_block = next_block
            next_block = block

            if current_block is None: continue

            classifed_block: DocumentBlock = current_block

            classifed_block.classified_type = self.classify_three_blocks(previous_block, current_block, next_block, index - 1).label

            classifed_blocks.append(classifed_block)

        return classifed_blocks

    def classify_three_blocks(
        self,
        previous_block: DocumentBlock,
        current_block: DocumentBlock,
        next_block: DocumentBlock,
        index,
    ) -> ClassificationResult:

        if not extracted_block_text(current_block):
            label = "empty"
            confidence = 0.0
            normalise_block = {}
        else:
            # print("classify", current_block)
            normalise_block = self.normalize_block_features(previous_block, current_block, next_block, index)

            label = "ml_predicted_2"
            confidence = 0.5

        return ClassificationResult(
            label=label,
            confidence=confidence,
            metadata={"source_type": current_block.parsed_block_data},
            normalise_block = normalise_block,
        )

    def train(self, blocks: List[Dict[str, Any]]):
        train_block_text = [extracted_block_text(block) for block in blocks]
        self.create_dictionary(train_block_text)

    def create_dictionary(self, train_blocks_text):
        """
        Создание и сохранение словаря TF-IDF
        """
        # Создание векторизатора
        vectorizer = TfidfVectorizer(
            tokenizer=custom_tokenizer,
            token_pattern=None,
            ngram_range=(1, 2),
            max_features=5000,
            min_df=3,
            max_df=0.85,
            sublinear_tf=True,
            norm="l2",
        )

        tfidf_matrix = vectorizer.fit_transform(train_blocks_text)
        joblib.dump(vectorizer, "modules/classification/model/tfidf_vectorizer.pkl")
        print(f"Словарь создан: {len(vectorizer.vocabulary_)} токенов")
        print(f"Матрица: {tfidf_matrix.shape}")

        return vectorizer

    def normalize_block_features(
        self,
        prev: Optional[DocumentBlock],
        curr: DocumentBlock,
        next_: Optional[DocumentBlock],
        index,
    ):
        """
            Нормализует признаки текстового блока для ML-классификатора.
            Возвращает словарь числовых признаков в диапазоне ~0..1.
            """

        # text_vector = self.all_vectors[index]

        # text = curr.get("data", {}).get("text", "") or ""

        # # if index > 690 and index < 697:
        # #     print("-------------------------")
        # #     print(f'Текст: "{text}"')
        # #     print("Вектор", text_vector)
        # #     print("Рассчитанный вектор", self.vectorizer.transform([text])[0])
        # #     print("-------------------------")

        # typo = curr.get("data", {}).get("typography", {}) or {}
        # geo = curr.get("geometry", {}) or {}

        # font_name = typo.get("font", "")
        # # font_size = typo.get("size_pt", base_font_size)
        # left_mm = geo.get("left_mm", 0)
        # top_mm = geo.get("top_mm", 0)
        # right_mm = geo.get("right_mm", 0)
        # bottom_mm = geo.get("bottom_mm", 0)

        # width_mm = right_mm - left_mm
        # height_mm = bottom_mm - top_mm

        # # --- Геометрия (нормализованная) ---
        # features = {
        #         # "norm_left_indent": left_mm / page_width_mm,
        #         # "norm_top_position": top_mm / page_height_mm,
        #         # "line_width_ratio": width_mm / page_width_mm,
        #         "line_height_mm": height_mm,
        #     }

        # # --- Типографика ---
        # # features["font_size_ratio"] = font_size / base_font_size
        # features["is_bold"] = (
        #         1.0 if any(m in font_name for m in ("Bold", "Bd", "Black")) else 0.0
        #     )
        # features["is_italic"] = (
        #         1.0 if any(m in font_name for m in ("Italic", "It", "Oblique")) else 0.0
        #     )

        # # --- Текст ---

        # # --- Контекст: предыдущий блок ---
        # if prev:
        #     prev_geo = prev.get("geometry", {})
        #     prev_typo = prev.get("data", {}).get("typography", {})
        #     prev_text = prev.get("data", {}).get("text", "") or ""
        #     prev_height = prev_geo.get("bottom_mm", 0) - prev_geo.get("top_mm", 0)
        #     prev_height = prev_height if prev_height > 0 else height_mm

        #     features["y_gap_ratio"] = (top_mm - prev_geo.get("bottom_mm", 0)) / prev_height
        #     # features["indent_diff_prev"] = (
        #     #         left_mm - prev_geo.get("left_mm", 0)
        #     #     ) / page_width_mm
        #     features["prev_same_style"] = (
        #             1.0 if font_name == prev_typo.get("font", "") else 0.0
        #         )
        #     features["prev_ends_terminal"] = (
        #             1.0 if prev_text.rstrip().endswith((".", "!", "?", ";")) else 0.0
        #         )
        #     # features["prev_font_size_ratio"] = (
        #     #         prev_typo.get("size_pt", base_font_size) / base_font_size
        #     #     )
        # else:
        #     features["y_gap_ratio"] = 0.0
        #     features["indent_diff_prev"] = 0.0
        #     features["prev_same_style"] = 0.0
        #     features["prev_ends_terminal"] = 0.0
        #     features["prev_font_size_ratio"] = 1.0

        # # --- Контекст: следующий блок ---
        # if next_:
        #     next_geo = next_.get("geometry", {})
        #     next_typo = next_.get("data", {}).get("typography", {})
        #     features["y_gap_next"] = (next_geo.get("top_mm", 0) - bottom_mm) / height_mm
        #     features["next_same_style"] = (
        #             1.0 if font_name == next_typo.get("font", "") else 0.0
        #         )
        # else:
        #     features["y_gap_next"] = 0.0
        #     features["next_same_style"] = 0.0

        # return features
