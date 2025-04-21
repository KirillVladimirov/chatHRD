#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для индексации документов с использованием современной системы на базе Haystack.
Использует систему индексации chathrd-index вместо устаревших парсеров.
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def index_documents(input_dir: str, index_dir: str, bm25_path: str) -> bool:
    """
    Запускает индексацию документов с использованием CLI команды chathrd-index.
    
    Args:
        input_dir: Директория с исходными файлами
        index_dir: Директория для сохранения индекса Chroma
        bm25_path: Путь для сохранения BM25 индекса
    
    Returns:
        bool: True если индексация успешна, иначе False
    """
    # Проверяем существование директории с исходными файлами
    input_path = Path(input_dir)
    if not input_path.exists():
        logger.error(f"Директория {input_dir} не существует")
        return False
    
    # Получаем список всех файлов в директории
    files = [f for f in input_path.glob('*') if f.is_file()]
    logger.info(f"Найдено {len(files)} файлов в {input_dir}")
    
    if not files:
        logger.warning(f"В директории нет файлов: {input_dir}")
        return False
    
    # Создаем директории для результатов, если они не существуют
    output_path = Path(index_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    bm25_output_path = Path(bm25_path)
    bm25_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Формируем команду для индексации
    cmd = [
        sys.executable, "-m", "chathrd.cli.index_command",
        "--data-dir", input_dir,
        "--index-dir", index_dir, 
        "--bm25-path", bm25_path,
        "--log-level", "INFO"
    ]
    
    # Запускаем индексацию
    logger.info(f"Запуск индексации для {len(files)} файлов...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("Индексация завершена успешно")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при индексации: {e}")
        logger.error(f"Вывод команды: {e.stdout}")
        logger.error(f"Ошибки: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return False

if __name__ == "__main__":
    # Директории для входных и выходных файлов
    input_dir = "data/downloaded_files"
    index_dir = "data/chroma_index"
    bm25_path = "data/bm25.pkl"
    
    # Запускаем индексацию
    success = index_documents(input_dir, index_dir, bm25_path)
    
    # Завершаем процесс с соответствующим кодом
    sys.exit(0 if success else 1) 