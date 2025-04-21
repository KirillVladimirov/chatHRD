"""Вспомогательные функции для работы с путями и файлами."""

import os
from pathlib import Path
from typing import Optional


def get_data_dir(data_dir: Optional[str] = None) -> Path:
    """
    Возвращает путь к директории с данными.
    
    Args:
        data_dir: Опционально - путь к директории с данными.
        
    Returns:
        Path: Путь к директории с данными.
    """
    if data_dir:
        path = Path(data_dir)
    else:
        # Сначала проверяем переменную окружения
        env_data_dir = os.getenv("DATA_DIR")
        if env_data_dir:
            path = Path(env_data_dir)
        else:
            # По умолчанию используем ../data/ относительно текущей директории
            path = Path(__file__).parent.parent.parent.parent / "data"
    
    # Создаем директорию, если она не существует
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_index_dir(index_dir: Optional[str] = None) -> Path:
    """
    Возвращает путь к директории с индексом.
    
    Args:
        index_dir: Опционально - путь к директории с индексом.
        
    Returns:
        Path: Путь к директории с индексом.
    """
    if index_dir:
        path = Path(index_dir)
    else:
        # Сначала проверяем переменную окружения
        env_index_dir = os.getenv("CHROMA_INDEX_PATH")
        if env_index_dir:
            path = Path(env_index_dir)
        else:
            # По умолчанию используем data/chroma_index/ относительно корня проекта
            path = get_data_dir() / "chroma_index"
    
    # Создаем директорию, если она не существует
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_bm25_path(bm25_path: Optional[str] = None) -> Path:
    """
    Возвращает путь к файлу индекса BM25.
    
    Args:
        bm25_path: Опционально - путь к файлу индекса BM25.
        
    Returns:
        Path: Путь к файлу индекса BM25.
    """
    if bm25_path:
        path = Path(bm25_path)
    else:
        # Сначала проверяем переменную окружения
        env_bm25_path = os.getenv("BM25_INDEX_PATH")
        if env_bm25_path:
            path = Path(env_bm25_path)
        else:
            # По умолчанию используем data/bm25.pkl относительно корня проекта
            path = get_data_dir() / "bm25.pkl"
    
    # Создаем родительскую директорию, если она не существует
    path.parent.mkdir(parents=True, exist_ok=True)
    return path 