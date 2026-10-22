import time
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
import torch
import torch.nn as nn
import torch.optim as optim
import os
import json


from ..document import (
    DocumentBlock,
    TextBlockData,
    BlockParsedType,
    BlockClassifiedType,
    NormalizeTextBlockData
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
        self.scalar_vector_length = None
        # self.all_vectors = None
        self.context_length = (15,4)
        self.path_vectorizer = 'modules/classification/model/tfidf_vectorizer.pkl'
        self.path_classifier = "modules/classification/model/bilstm_classifier.pth"

# ============================================================
# region Классификация
# ============================================================

    def classify(self, blocks: List[DocumentBlock]) -> List[DocumentBlock]:


        self.load_tfidf()
        self.load_bilstm()

        X = self.get_matrix(blocks)  
    
        predictions = self.predict_bilstm(X)

        for block, predicted_idx in zip(blocks, predictions):
            block.classified_type = list(BlockClassifiedType)[predicted_idx]

        return blocks


    def get_matrix(self, blocks: List[DocumentBlock]):
        X = []

        block_text = [extracted_block_text(block) for block in blocks]
        
        # Сразу получаем плотную матрицу, toarray() ускорит работу
        tfidf_matrix = self.vectorizer.transform(block_text).toarray() 
        
        for block_idx, block in enumerate(blocks):
            # Вектор нормализованных признаков (шрифты, размеры, отступы)
            scalar_vec = block.normalized_data.to_vector()

            if self.scalar_vector_length is None:
                self.scalar_vector_length = len(scalar_vec)

            # Текстовый вектор (только для ЭТОГО блока)
            text_vec = tfidf_matrix[block_idx]

            
            # Склеиваем только признаки самого блока, без соседей!
            full_vector = np.concatenate([scalar_vec, text_vec])
            X.append(full_vector)
        
        # 1. Превращаем 2D numpy-массив в тензор PyTorch
        tensor_2d = torch.tensor(np.array(X), dtype=torch.float32)
        
        # 2. Добавляем размерность батча (unsqueeze) и отдаем 3D-матрицу (1, seq_len, features)
        return tensor_2d.unsqueeze(0)

# ============================================================
# region Обучение
# ============================================================            
        
    def train(self, docs_blocks: List[List[DocumentBlock]]):
        all_train_texts = []
        for doc in docs_blocks:
            for block in doc:
                if (block.classified_type is not None and 
                    block.parsed_type == BlockParsedType.TEXT and 
                    block.normalized_data is not None):
                    all_train_texts.append(extracted_block_text(block))
        
        if len(all_train_texts) < 1: 
            print("ОШИБКА: Нет размеченных данных для обучения")
            return

        self.create_tfidf()
        self.create_dictionary(all_train_texts)

        num_scalar_features = len(docs_blocks[0][0].normalized_data.to_vector())
        
        # Ищем первый валидный документ со строгой фильтрацией
        sample_doc = []
        for doc in docs_blocks:
            sample_doc = [
                b for b in doc 
                if b.classified_type is not None 
                and b.parsed_type == BlockParsedType.TEXT
                and b.normalized_data is not None
            ]
            if sample_doc:
                break
                
        if not sample_doc:
            print("ОШИБКА: Во всех документах нет размеченных данных для определения размерности")
            return

        sample_matrix = self.get_matrix(sample_doc)
        input_dim = sample_matrix.shape[-1]
        vocab_size = len(self.vectorizer.get_feature_names_out())
        num_classes = len(BlockClassifiedType)

        print(f"Инициализация BiLSTM (Multi-branch). Скаляров: {num_scalar_features}, Словарь: {vocab_size}, Классов: {num_classes}")

        self.create_bilstm(
            num_scalar_features=num_scalar_features,
            vocab_size=vocab_size,
            num_classes=num_classes
        )
        self.train_bilstm(docs_blocks, epochs=55, lr=0.001)


        self.save_bilstm()
        self.save_tfidf()

# ============================================================
# region Тест
# ============================================================

    def test(self, docs_blocks: List[List[DocumentBlock]]):
        """Тестирование модели на массиве документов"""
        # 1. Загружаем словарь TF-IDF
        self.load_tfidf()

        # Получаем размерности на основе первого валидного документа
        sample_doc = [b for b in docs_blocks[0] if b.classified_type is not None]
        if not sample_doc:
            print("ОШИБКА: Первый документ не содержит размеченных данных для определения размерности")
            return
        
        # 2. Загружаем веса модели
        self.load_bilstm()

        all_true_labels = []
        all_predictions = []
        
        start_time = time.time()

        # 3. Делаем предсказания для каждого документа по отдельности
        for doc in docs_blocks:
            valid_blocks = [
                b for b in doc 
                if b.classified_type is not None 
                and b.parsed_type == BlockParsedType.TEXT
                and b.normalized_data is not None
            ]
            if not valid_blocks:
                continue

            X_doc = self.get_matrix(valid_blocks)
            Y_doc = [BlockClassifiedType.index(block.classified_type) for block in valid_blocks]

            # Предсказание для одной последовательности (одного документа)
            doc_predictions = self.predict_bilstm(X_doc)

            all_true_labels.extend(Y_doc)
            all_predictions.extend(doc_predictions)

        if not all_true_labels:
            print("ОШИБКА: Нет размеченных данных для тестирования во всех документах")
            return

        # 4. Оценка точности по всем документам
        test_accuracy = accuracy_score(all_true_labels, all_predictions)
        
        print(f"\n{'='*30}")
        print(f"ДОКУМЕНТОВ В ТЕСТЕ: {len(docs_blocks)}")
        print(f"{'='*30}")
        print(f"ОБЩЕЕ КОЛИЧЕСТВО БЛОКОВ: {sum(len(doc) for doc in docs_blocks)}")
        print(f"{'='*30}")
        print(f"ОБЩАЯ ТОЧНОСТЬ: {test_accuracy:.2%}")
        print(f"{'='*30}")
        print(f"ВРЕМЯ ПРЕДСКАЗАНИЯ: {time.time() - start_time:.2f} с")
        print(f"{'='*30}")


# ============================================================
# region BiLSTM
# ============================================================

    def create_bilstm(self, num_scalar_features: int, vocab_size: int, num_classes: int, hidden_dim: int = 64):
        """Создание архитектуры BiLSTM"""
        # Автоматический выбор видеокарты, если она есть (CUDA/MPS), иначе процессор
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.bilstm_model = DocumentSequenceClassifier(
            num_scalar_features=num_scalar_features,
            vocab_size=vocab_size,
            hidden_dim=hidden_dim, 
            num_classes=num_classes
        ).to(self.device)

    
    def train_bilstm(self, docs_blocks: List[List[DocumentBlock]], epochs=20, lr=0.001):
        self.bilstm_model.train()
        optimizer = torch.optim.Adam(self.bilstm_model.parameters(), lr=lr)
        criterion = torch.nn.CrossEntropyLoss()

        for epoch in range(epochs):
            epoch_loss = 0.0
            
            for doc in docs_blocks:
                # Строгая фильтрация, аналогично classify/test
                valid_blocks = [
                    b for b in doc 
                    if b.classified_type is not None 
                    and b.parsed_type == BlockParsedType.TEXT
                    and b.normalized_data is not None
                ]
                if not valid_blocks:
                    continue

                X_tensor = self.get_matrix(valid_blocks).to(self.device)
                
                # Исправлено: используем list(BlockClassifiedType).index() вместо .index() у типа
                Y_doc = [BlockClassifiedType.index(b.classified_type) for b in valid_blocks]
                Y_tensor = torch.tensor(Y_doc, dtype=torch.long).unsqueeze(0).to(self.device)

                optimizer.zero_grad()
                outputs = self.bilstm_model(X_tensor) 
                
                loss = criterion(outputs.view(-1, len(BlockClassifiedType)), Y_tensor.view(-1))
                
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                
            if (epoch + 1) % 5 == 0 or epoch == 0:
                print(f"BiLSTM Эпоха [{epoch+1}/{epochs}] | Loss: {epoch_loss / len(docs_blocks):.4f}")



    def predict_bilstm(self, X, return_proba=False):
        self.bilstm_model.eval()
        with torch.no_grad():
            # Просто переносим готовый 3D-тензор на устройство
            X_tensor = X.clone().detach().to(self.device) 
            
            # Получаем предсказания и убираем измерение батча для возврата плоского списка
            logits = self.bilstm_model(X_tensor).squeeze(0)
            if return_proba:
                probabilities = torch.softmax(logits, dim=1)
                return probabilities.cpu().numpy()
            
            # Выбираем класс с максимальной вероятностью для каждого блока
            predictions = torch.argmax(logits, dim=1)
            return predictions.cpu().numpy()

        


    def save_bilstm(self):
        os.makedirs(os.path.dirname(self.path_classifier), exist_ok=True)
        torch.save(self.bilstm_model.state_dict(), self.path_classifier)
        
        config = {
            "num_scalar_features": self.bilstm_model.scalar_compressor[0].in_features,
            "vocab_size": self.bilstm_model.text_compressor[0].in_features,
            "hidden_dim": self.bilstm_model.lstm.hidden_size,
            "num_classes": self.bilstm_model.fc.out_features
        }
        config_path = self.path_classifier.replace('.pth', '_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f)


    def load_bilstm(self):
        config_path = self.path_classifier.replace('.pth', '_config.json')
        if not os.path.exists(config_path):
            raise FileNotFoundError("Не найден файл конфигурации для загрузки модели!")
            
        # 1. Читаем настройки из файла
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # 2. Создаем пустой скелет по прочитанным настройкам
        self.create_bilstm(
            num_scalar_features=config.get('num_scalar_features', self.scalar_vector_length),
            vocab_size=config.get('vocab_size', len(self.vectorizer.get_feature_names_out()) if self.vectorizer else 0),
            num_classes=config['num_classes'],
            hidden_dim=config['hidden_dim']
        )
        
        # 3. Натягиваем сохраненные веса на этот скелет
        state_dict = torch.load(self.path_classifier, map_location=self.device)
        self.bilstm_model.load_state_dict(state_dict)
        self.bilstm_model.eval()



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
            min_df=1,
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

    def save_tfidf(self):
        joblib.dump(self.vectorizer, self.path_vectorizer)

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


class DocumentSequenceClassifier(nn.Module):
    def __init__(self, num_scalar_features: int, vocab_size: int, hidden_dim: int, num_classes: int):
        super(DocumentSequenceClassifier, self).__init__()
        
        # 1. Выделенная ветка для геометрических/шрифтовых признаков (18 штук)
        scalar_out_dim = 32
        self.scalar_compressor = nn.Sequential(
            nn.Linear(num_scalar_features, scalar_out_dim),
            nn.ReLU()
        )
        
        # 2. Выделенная ветка для текстовых признаков (TF-IDF словарь)
        text_out_dim = 224
        self.text_compressor = nn.Sequential(
            nn.Linear(vocab_size, text_out_dim),
            nn.ReLU(),
            nn.Dropout(p=0.4)
        )
        
        # Суммарная размерность после объединения: 32 + 224 = 256
        compressed_dim = scalar_out_dim + text_out_dim
        
        # 3. Двунаправленная LSTM принимает сжатые признаки
        self.lstm = nn.LSTM(
            input_size=compressed_dim,
            hidden_size=hidden_dim,
            batch_first=True,
            bidirectional=True
        )
        
        # 4. Классификатор
        self.fc = nn.Linear(hidden_dim * 2, num_classes)

    def forward(self, x):
        # x приходит в виде единого тензора: [Batch, Seq_Len, num_scalars + vocab_size]
        num_scalars = self.scalar_compressor[0].in_features
        
        # Разделяем входной поток на геометрию и текст
        scalar_part = x[:, :, :num_scalars]
        text_part = x[:, :, num_scalars:]
        
        # Прогоняем параллельно через независимые слои
        scalar_dense = self.scalar_compressor(scalar_part)
        text_dense = self.text_compressor(text_part)
        
        # Объединяем в единый вектор
        dense_features = torch.cat([scalar_dense, text_dense], dim=-1)
        
        # Дальше стандартно через LSTM и полносвязный слой
        lstm_out, _ = self.lstm(dense_features)
        out = self.fc(lstm_out)
        return out