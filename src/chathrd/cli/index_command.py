"""Командный интерфейс для запуска индексации документов."""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Optional

from chathrd.pipelines.indexing import run_indexing


def parse_arguments() -> argparse.Namespace:
    """
    Парсит аргументы командной строки.
    
    Returns:
        argparse.Namespace: Аргументы командной строки.
    """
    parser = argparse.ArgumentParser(
        description="Индексация документов для поиска.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "files", 
        nargs="*",
        help="Пути к файлам для индексации. Если не указаны, будут использоваться все файлы из директории data_dir."
    )
    parser.add_argument(
        "--data-dir", 
        default="../data/downloaded_files",
        help="Директория с файлами для индексации (если не указаны конкретные файлы)."
    )
    parser.add_argument(
        "--index-dir",
        default="../data/chroma_index",
        help="Директория для сохранения индекса."
    )
    parser.add_argument(
        "--bm25-path",
        default="../data/bm25.pkl",
        help="Путь для сохранения BM25 индекса."
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Уровень логирования."
    )
    return parser.parse_args()


def setup_logging(log_level: str) -> None:
    """
    Настраивает логирование.
    
    Args:
        log_level: Уровень логирования.
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Неверный уровень логирования: {log_level}")
        
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def validate_paths(files: List[str], data_dir: str) -> Optional[List[str]]:
    """
    Проверяет существование путей.
    
    Args:
        files: Список путей к файлам.
        data_dir: Директория с данными.
        
    Returns:
        Optional[List[str]]: Список существующих путей или None в случае ошибки.
    """
    if files:
        # Проверяем, что все указанные файлы существуют
        missing_files = [f for f in files if not os.path.exists(f)]
        if missing_files:
            logging.error(f"Не найдены следующие файлы: {', '.join(missing_files)}")
            return None
        return files
    
    # Если файлы не указаны, проверяем существование директории
    if not os.path.isdir(data_dir):
        logging.error(f"Директория не существует: {data_dir}")
        return None
        
    # Проверяем, что в директории есть файлы
    files_in_dir = [os.path.join(data_dir, f) for f in os.listdir(data_dir) 
                   if os.path.isfile(os.path.join(data_dir, f))]
    if not files_in_dir:
        logging.error(f"В директории нет файлов: {data_dir}")
        return None
        
    return files_in_dir


def main() -> int:
    """
    Основная функция для запуска индексации.
    
    Returns:
        int: Код завершения (0 - успех, 1 - ошибка).
    """
    args = parse_arguments()
    setup_logging(args.log_level)
    
    logging.info("Запуск индексации документов")
    
    # Создаем все необходимые директории
    Path(args.index_dir).parent.mkdir(parents=True, exist_ok=True)
    Path(args.bm25_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Проверяем пути
    files = validate_paths(args.files, args.data_dir)
    if files is None:
        return 1
    
    # Запускаем индексацию
    try:
        run_indexing(file_paths=files, data_dir=args.data_dir)
        logging.info("Индексация завершена успешно")
        return 0
    except Exception as e:
        logging.error(f"Ошибка при индексации: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 