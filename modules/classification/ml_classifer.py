from typing import Any, Dict, List, Optional
from .base import BaseClassifier, ClassificationResult

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from nltk.tokenize import WordPunctTokenizer
from nltk.corpus import stopwords
from collections import Counter
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
        # self.all_vectors = None
        self.context_length = (1,1)
        self.path_vectorizer = 'modules/classification/model/tfidf_vectorizer.pkl'
        self.path_classifier = "modules/classification/model/rf_classifier.pkl"

# region Классификация

    def classify(self, blocks: List[DocumentBlock]) -> List[DocumentBlock]:


        self.load_tfidf()
        self.load_rf()

        X = self.get_matrix(blocks)  

        predictions = self.predict_rf(X)

        for block, predicted_class in zip(blocks, predictions):
            block.classified_type = predicted_class


        return blocks

    def get_matrix(self, blocks: List[DocumentBlock]):
        X = []
        block_text = [extracted_block_text(block) for block in blocks]
        tfidf_matrix = self.vectorizer.transform(block_text)
        
        scalar_len = len(blocks[0].normalized_data.to_vector())
        text_len = tfidf_matrix.shape[1]
        zero_vector = np.zeros(scalar_len + text_len)

        for block_idx, block in enumerate(blocks):
            blocks_vectors = []
            
            for offset in range(-self.context_length[0], self.context_length[1] + 1):
                curr_idx = block_idx + offset
            
                if 0 <= curr_idx < len(blocks):
                    # Берем и скаляры, и текст ВСЕХ блоков в окне
                    scalar_vec = blocks[curr_idx].normalized_data.to_vector()
                    text_vec = tfidf_matrix[curr_idx].toarray().flatten()
                    blocks_vectors.append(np.concatenate([scalar_vec, text_vec]))
                else:
                    # Если вышли за границы, добавляем нули правильной длины
                    blocks_vectors.append(zero_vector)

            # Склеиваем всё окно в один вектор для текущего блока
            full_vector = np.concatenate(blocks_vectors)
            X.append(full_vector)
        
        return np.array(X)
            

    # def classify_one_block(
    #     self,
    #     current_block: DocumentBlock,
    #     index,
    # ):

    #     text_vector = self.all_vectors[index].toarray().flatten().tolist()
    #     block_patterns = current_block.normalized_data.to_vector()
    
    #     vector = np.concatenate([block_patterns, text_vector]) 

    #     ml_predict = self.predict_rf(vector.reshape(1, -1))
        
    #     current_block.classified_type = ml_predict[0]

        
    def train(self, blocks: List[DocumentBlock]):
        blocks = [
            block for block in blocks 
            if block.classified_type is not None 
            and block.normalized_data is not None
        ]
        if(len(blocks) < 1): return

        block_text = [extracted_block_text(block) for block in blocks]
        self.create_tfidf()
        self.create_dictionary(block_text)

        X_train = self.get_matrix(blocks)
        Y_train = np.array([block.classified_type.value for block in blocks])

        if(len(Y_train) < 1): print("ОШИБКА- В документе нет размеченых данных")

        X_train = np.array(X_train)
        Y_train = np.array(Y_train)
        
        print(f"Матрица: {X_train.shape}")
        
        self.create_rf()
        self.train_rf(X_train, Y_train)

        self.save_rf("modules/classification/model/rf_classifier.pkl")
        self.save_tfidf("modules/classification/model/tfidf_vectorizer.pkl")

        

    def test(self, blocks: List[DocumentBlock]):
        blocks = [
            block for block in blocks 
            if block.classified_type is not None 
            and block.normalized_data is not None
        ]
        if(len(blocks) < 1): return

        self.load_tfidf()
        self.load_rf()

        X_test = self.get_matrix(blocks)
        Y_test = np.array([block.classified_type.value for block in blocks])

        if(len(Y_test) < 1): print("ОШИБКА- В документе нет размеченых данных")

        # 1. Предсказания на обучающей выборке
        train_predictions = self.rf_model.predict(X_test)
        
        # 2. Точность на обучающих данных
        train_accuracy = accuracy_score(Y_test, train_predictions)
        print(f"\n{'='*60}")
        print(f"ТОЧНОСТЬ НА ОБУЧАЮЩЕЙ ВЫБОРКЕ: {train_accuracy:.2%}")
        print(f"{'='*60}")
        
        # 3. Отчёт по классам
        print("\nОТЧЁТ ПО КЛАССАМ:")
        print(classification_report(
            Y_test, train_predictions, 
            labels=self.rf_model.classes_,
            target_names=self.rf_model.classes_,
            digits=3,
            zero_division=0 
        ))

        print("Классы в Y_test:", set(Y_test))
        print("Классы в предсказаниях:", set(train_predictions))
        print("Классы модели:", self.rf_model.classes_)
        
        # 4. Матрица ошибок
        print("МАТРИЦА ОШИБОК (confusion matrix):")
        cm = confusion_matrix(Y_test, train_predictions)
        print(cm)
        
        # 5. Распределение классов
        print("\nРАСПРЕДЕЛЕНИЕ КЛАССОВ В ВЫБОРКЕ:")
        class_counts = Counter(Y_test)
        for cls, count in sorted(class_counts.items(), key=lambda x: -x[1]):
            print(f"  {cls:25s}: {count:4d} ({count/len(Y_test)*100:5.1f}%)")
        
        # 6. Топ-10 самых неуверенных предсказаний
        proba = self.rf_model.predict_proba(X_test)
        max_probs = np.max(proba, axis=1)
        uncertain_indices = np.argsort(max_probs)[:10]  # 10 самых неуверенных
        
        print("\nСАМЫЕ СЛОЖНЫЕ КЛАССЫ:")
        from collections import defaultdict

        conf_by_class = defaultdict(list)
        for t, c in zip(Y_test, max_probs):
            conf_by_class[t].append(c)
       
        for cls, confs in sorted(conf_by_class.items(), key=lambda x: np.mean(x[1]))[:10]:
            print(f"  {cls:<25s} : {np.mean(confs):.3f} ( n={len(confs)})")

# endregion
# ============================================================
# region Random Forest
# ============================================================


    def create_rf(self):
        self.rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=None,
            min_samples_split=2,
            random_state=42,
            n_jobs=-1
        )
    
    def train_rf(self, X_train, y_train):
        """Обучение Random Forest на нормализованных признаках строк"""
        self.rf_model.fit(X_train, y_train)
        
    def save_rf(self, filepath):
        """Сохранение обученной модели RF"""
        joblib.dump(self.rf_model, filepath)
    
    def load_rf(self):
        """Загрузка модели RF"""
        self.rf_model = joblib.load(self.path_classifier)
    
    def predict_rf(self, X, return_proba=False):
        """Классификация строк (для передачи в CRF)"""
        if return_proba:
            return self.rf_model.predict_proba(X)
        return self.rf_model.predict(X)


# endregion
# ============================================================
#  region Словарь
# ============================================================


    def create_tfidf(self):
        """Создание и сохранение словаря TF-IDF"""
        
        self.vectorizer = TfidfVectorizer(
            tokenizer=custom_tokenizer,
            token_pattern=None,
            ngram_range=(1, 2),
            max_features=5000,
            min_df=3,
            max_df=0.85,
            sublinear_tf=True,
            norm="l2",
        )

        # tfidf_matrix = vectorizer.fit_transform(train_blocks_text)
        # joblib.dump(vectorizer, "modules/classification/model/tfidf_vectorizer.pkl")
        # print(f"Словарь создан: {len(vectorizer.vocabulary_)} токенов")
        # print(f"Матрица: {tfidf_matrix.shape}")

        # return vectorizer


    def create_dictionary(self, train_blocks_text):
        self.vectorizer.fit_transform(train_blocks_text)
        print(f"Словарь создан: {len(self.vectorizer.vocabulary_)} токенов")

    def save_tfidf(self, path):
        joblib.dump(self.vectorizer, path)

    def load_tfidf(self):
        self.vectorizer = joblib.load(self.path_vectorizer)

# endregion
# ============================================================
#  region Вспомогательные
# ============================================================



def custom_tokenizer(text):
    text = str(text).lower()
    pattern = r"(\d+(?:\.\d+)*[\.)]?|[•\-\—\–]|[а-яa-z]+|[.,;:!?(){}\[\]\"'])"
    tokens = re.findall(pattern, text)

    result = []
    for token in tokens:
        if token in stop_words:
            continue
        if re.search(r"\d+", token):
            normalized = re.sub(r"\d+", "n", token)
            result.append(normalized)
        elif re.match(r"^[а-яa-z]{1,}$", token):
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