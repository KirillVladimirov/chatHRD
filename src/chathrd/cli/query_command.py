"""Командный интерфейс для выполнения запросов к индексированным документам."""

import sys
import logging
import argparse
from pathlib import Path
from typing import Optional

from chathrd.pipelines.querying import process_query, create_querying_pipeline


def parse_arguments() -> argparse.Namespace:
    """
    Парсит аргументы командной строки.
    
    Returns:
        argparse.Namespace: Аргументы командной строки.
    """
    parser = argparse.ArgumentParser(
        description="Выполнение запросов к индексированным документам.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "query", 
        help="Текст запроса для поиска информации."
    )
    parser.add_argument(
        "--model-name",
        default=None,
        help="Имя модели LLM для генерации ответов."
    )
    parser.add_argument(
        "--api-url",
        default=None,
        help="URL для API LLM."
    )
    parser.add_argument(
        "--index-dir",
        default="../data/chroma_index",
        help="Директория с индексом Chroma."
    )
    parser.add_argument(
        "--bm25-path",
        default="../data/bm25.pkl",
        help="Путь к индексу BM25."
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


def validate_paths(index_dir: str, bm25_path: str) -> bool:
    """
    Проверяет существование путей.
    
    Args:
        index_dir: Путь к индексу Chroma.
        bm25_path: Путь к индексу BM25.
        
    Returns:
        bool: True, если все пути существуют, иначе False.
    """
    # Проверяем директорию с индексом Chroma
    if not Path(index_dir).exists():
        logging.error(f"Директория с индексом Chroma не найдена: {index_dir}")
        return False
    
    # Проверяем файл с индексом BM25
    if not Path(bm25_path).exists():
        logging.error(f"Файл с индексом BM25 не найден: {bm25_path}")
        return False
    
    return True


def main() -> int:
    """
    Основная функция для выполнения запросов.
    
    Returns:
        int: Код завершения (0 - успех, 1 - ошибка).
    """
    args = parse_arguments()
    setup_logging(args.log_level)
    
    logging.info(f"Выполнение запроса: {args.query}")
    
    # Проверяем наличие индексов
    if not validate_paths(args.index_dir, args.bm25_path):
        logging.error("Не найдены необходимые индексы. Сначала выполните индексацию документов.")
        return 1
    
    # Создаем пайплайн для запросов
    try:
        # Получаем опциональные параметры из конфига или аргументов
        from chathrd.config.settings import settings
        
        model_name = args.model_name or settings.MODEL_NAME
        api_url = args.api_url or settings.LLM_API_URL
        
        logging.info(f"Используемые параметры: model_name={model_name}, api_url={api_url}")
        
        pipeline = create_querying_pipeline(
            model_name=model_name,
            api_url=api_url,
            persist_path=args.index_dir,
            bm25_path=args.bm25_path
        )
        
        # Выполняем запрос
        result = process_query(args.query, pipeline)
        
        # Выводим результат
        answer = result.get("answer", "Не удалось найти ответ на ваш запрос.")
        print("\n" + "-" * 80 + "\n")
        print(answer)
        print("\n" + "-" * 80)
        
        logging.info("Запрос выполнен успешно")
        return 0
    except Exception as e:
        logging.error(f"Ошибка при выполнении запроса: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 