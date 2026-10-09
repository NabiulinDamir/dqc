from typing import Any, Dict, List, Optional
from .base import BaseClassifier, ClassificationResult

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from nltk.tokenize import WordPunctTokenizer
from nltk.corpus import stopwords
import numpy as np
import pymorphy3
import joblib
import re

from ..document import (
    DocumentBlock,
    TextBlockData,
    BlockParsedType,
    BlockClassifiedType
)

# Инициализация инструментов
morph = pymorphy3.MorphAnalyzer()
tokenizer = WordPunctTokenizer()
stop_words = set(stopwords.words('russian'))


class MlClassifier(BaseClassifier):

    def __init__(self):
        super().__init__(name="ml")
        self.rf_model = None
        self.vectorizer = None
        self.all_vectors = None

# region Классификация

    def classify(self, blocks: List[DocumentBlock]):
        path = 'modules/classification/model/tfidf_vectorizer.pkl'

        self.vectorizer = joblib.load(path)
        all_texts = [extracted_block_text(block) for block in blocks]
        self.all_vectors = self.vectorizer.transform(all_texts)

        print("Вектор документа создан")
        print(f"Матрица: {self.all_vectors.shape}")

        for index, block in enumerate(blocks):
            block.normalized_data.prev_block_classified_type = BlockClassifiedType.index(blocks[index-1].classified_type)
            self.classify_one_block(block, index)
            

    def classify_one_block(
        self,
        current_block: DocumentBlock,
        index,
    ):

        text_vector = self.all_vectors[index].toarray().flatten().tolist()
        block_patterns = current_block.normalized_data.to_vector()
        vector = np.concatenate([block_patterns, text_vector]) 

        # ml_pledict = self.predict_rf(vector)
        
        current_block.classified_type = BlockClassifiedType.TEXT

        

    def train(self, blocks: List[DocumentBlock]):
        # Создание нового словаря
        train_block_text = [extracted_block_text(block) for block in blocks]
        self.create_dictionary(train_block_text)
        # Создание нового классификатора
        self.rf_model = self.get_new_model()

        X_train = np.array([
            block.normalized_data.to_vector() 
            for block in blocks 
            if block.normalized_data is not None
        ])

        # self.train_rf()


# endregion
# ============================================================
# region Random Forest
# ============================================================


    def get_new_model():
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=None,
            min_samples_split=2,
            random_state=42,
            n_jobs=-1
        )
        return rf_model
    
    def train_rf(self, X_train, y_train):
        """Обучение Random Forest на нормализованных признаках строк"""
        self.rf_model.fit(X_train, y_train)
        
    def save_rf(self, filepath):
        """Сохранение обученной модели RF"""
        joblib.dump(self.rf_model, filepath)
    
    def load_rf(self, filepath):
        """Загрузка модели RF"""
        self.rf_model = joblib.load(filepath)
    
    def predict_rf(self, X, return_proba=False):
        """Классификация строк (для передачи в CRF)"""
        if return_proba:
            return self.rf_model.predict_proba(X)
        return self.rf_model.predict(X)


# endregion
# ============================================================
#  region Словарь
# ============================================================


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
# ============================================================
#  region Вспомогательные
# ============================================================



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