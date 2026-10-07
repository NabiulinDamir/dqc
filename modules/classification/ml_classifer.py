from typing import Any, Dict, List, Optional
from .base import BaseClassifier, ClassificationResult

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
import pymorphy3
from nltk.tokenize import WordPunctTokenizer
from nltk.corpus import stopwords
import re

from ..document import (
    DocumentBlock,
    TextBlockData,
    BlockParsedType
)

# Инициализация инструментов
morph = pymorphy3.MorphAnalyzer()
tokenizer = WordPunctTokenizer()
stop_words = set(stopwords.words('russian'))


class MlClassifier(BaseClassifier):

    def __init__(self):
        super().__init__(name="ml")
        self.vectorizer = None
        self.all_vectors = None

# region Классификация

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

        result = ClassificationResult(label="empty", confidence=0.0, metadata={})

        if (current_block.parsed_type == BlockParsedType.IMAGE):
            result.label = "image"
            result.confidence = 0.0
        elif (current_block.parsed_type == BlockParsedType.TABLE):
            result.label = "table"
            result.confidence = 0.0
        else:
            # current_block.normalized_data.text_vector = self.all_vectors[index].toarray().flatten().tolist()
            result.label = "ml_predicted_2"
            result.confidence = 0.5

        return result



# endregion
# region Векторизатор



    def train(self, blocks: List[Dict[str, Any]]):
        # Создание нового словаря
        train_block_text = [extracted_block_text(block) for block in blocks]
        self.create_dictionary(train_block_text)

        # 

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



# endregion
# region Вспомагательные



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
    if block and isinstance(block.parsed_data.data, TextBlockData):
        text = block.parsed_data.data.text or "emptyText"
    else:
        text = "emptyText"
    return text