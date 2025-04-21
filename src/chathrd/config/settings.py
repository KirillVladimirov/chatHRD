"""Настройки приложения."""

import os
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла (если он существует)
load_dotenv()


class Settings:
    """Класс для хранения настроек приложения."""
    
    # Директории для данных
    DATA_DIR: str = os.getenv("DATA_DIR", "../data")
    DOWNLOADED_FILES_DIR: str = os.getenv("DOWNLOADED_FILES_DIR", os.path.join(DATA_DIR, "downloaded_files"))
    
    # Пути к индексам
    CHROMA_INDEX_PATH: str = os.getenv("CHROMA_INDEX_PATH", os.path.join(DATA_DIR, "chroma_index"))
    BM25_INDEX_PATH: str = os.getenv("BM25_INDEX_PATH", os.path.join(DATA_DIR, "bm25.pkl"))
    
    # Настройки LLM
    MODEL_NAME: str = os.getenv("MODEL_NAME", "hf.co/IlyaGusev/saiga_yandexgpt_8b_gguf:Q4_0")
    LLM_API_URL: str = os.getenv("LLM_API_URL", "http://localhost:11434/v1")
    
    # Настройки векторизации
    EMBEDDER_MODEL: str = os.getenv(
        "EMBEDDER_MODEL", 
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    
    # Настройки индексации
    MAX_SPLIT_LENGTH: int = int(os.getenv("MAX_SPLIT_LENGTH", "200"))
    SPLIT_OVERLAP: int = int(os.getenv("SPLIT_OVERLAP", "50"))
    
    # Настройки поиска
    TOP_K_RETRIEVAL: int = int(os.getenv("TOP_K_RETRIEVAL", "5"))
    TOP_K_RANKER: int = int(os.getenv("TOP_K_RANKER", "5"))
    RANKER_MODEL: str = os.getenv(
        "RANKER_MODEL", 
        "cross-encoder/ms-marco-TinyBERT-L-2-v2"
    )
    
    # Настройки генерации
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.8"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1000"))
    TIMEOUT: int = int(os.getenv("TIMEOUT", "60"))
    
    # Настройки Telegram бота
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """
        Преобразует настройки в словарь.
        
        Returns:
            Dict[str, Any]: Словарь настроек.
        """
        return {
            key: value for key, value in cls.__dict__.items() 
            if key.isupper() and not key.startswith("_")
        }
    
    @classmethod
    def create_dirs(cls) -> None:
        """Создает все необходимые директории."""
        Path(cls.DATA_DIR).mkdir(parents=True, exist_ok=True)
        Path(cls.DOWNLOADED_FILES_DIR).mkdir(parents=True, exist_ok=True)
        Path(cls.CHROMA_INDEX_PATH).mkdir(parents=True, exist_ok=True)
        Path(os.path.dirname(cls.BM25_INDEX_PATH)).mkdir(parents=True, exist_ok=True)


# Экземпляр настроек для использования в приложении
settings = Settings()

# Создаем директории при импорте модуля
settings.create_dirs()