#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from pathlib import Path
from chathrd.parsers.base import parse_file

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_files_to_process(input_dir: str, output_dir: str) -> list:
    """
    Получает список файлов, которые требуют обработки.
    
    Args:
        input_dir: Директория с исходными файлами
        output_dir: Директория с уже обработанными файлами
    
    Returns:
        list: Список путей к файлам, которые нужно обработать
    """
    # Получаем все файлы из директории с исходными документами
    input_path = Path(input_dir)
    if not input_path.exists():
        logger.error(f"Директория {input_dir} не существует")
        return []
    
    # Получаем список всех файлов в директории
    all_files = [f for f in input_path.glob('*') if f.is_file()]
    logger.info(f"Всего найдено {len(all_files)} файлов в {input_dir}")
    
    # Получаем список уже обработанных файлов
    output_path = Path(output_dir)
    processed_files = set()
    if output_path.exists():
        # Извлекаем только названия файлов без расширения .md
        processed_files = {f.stem for f in output_path.glob('*.md')}
        logger.info(f"Найдено {len(processed_files)} уже обработанных файлов в {output_dir}")
    
    # Фильтруем список, исключая уже обработанные файлы
    files_to_process = [f for f in all_files if f.stem not in processed_files]
    
    # Сортируем файлы по размеру (от меньшего к большему)
    files_to_process.sort(key=lambda f: f.stat().st_size)
    
    logger.info(f"Требуют обработки {len(files_to_process)} файлов (отсортированы от меньшего к большему)")
    
    return files_to_process

def process_files(files: list, output_dir: str):
    """
    Обрабатывает файлы и сохраняет результаты в markdown формате.
    
    Args:
        files: Список объектов Path для обработки
        output_dir: Директория для сохранения результатов
    """
    # Создаем директорию для результатов, если она не существует
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Счетчики для статистики
    successful = 0
    failed = 0
    skipped = 0
    total = len(files)
    
    # Обрабатываем каждый файл
    for idx, file_path in enumerate(files, 1):
        # Логируем прогресс с информацией о размере файла
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        logger.info(f"Обработка файла [{idx}/{total}]: {file_path} ({file_size_mb:.2f} МБ)")
        
        try:
            # Парсим файл
            content = parse_file(str(file_path))
            
            # Если содержимое None, значит файл не может быть обработан поддерживаемым парсером
            if content is None:
                logger.warning(f"[{idx}/{total}] Пропущен неподдерживаемый формат: {file_path}")
                skipped += 1
                continue
                
            # Сохраняем результат
            output_file = output_path / f"{file_path.stem}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"[{idx}/{total}] Успешно обработан файл: {file_path}")
            successful += 1
            
        except Exception as e:
            logger.error(f"[{idx}/{total}] Ошибка при обработке файла {file_path}: {e}")
            failed += 1
    
    # Выводим итоговую статистику
    logger.info(f"Обработка завершена. Успешно: {successful}, С ошибками: {failed}, Пропущено: {skipped}, Всего: {total}")

if __name__ == "__main__":
    # Директории для входных и выходных файлов
    input_dir = "data/downloaded_files"
    output_dir = "data/parsed_files"
    
    # Получаем список файлов для обработки
    files_to_process = get_files_to_process(input_dir, output_dir)
    
    # Если есть файлы для обработки, обрабатываем их
    if files_to_process:
        logger.info(f"Начинаем обработку {len(files_to_process)} файлов...")
        process_files(files_to_process, output_dir)
    else:
        logger.info("Нет новых файлов для обработки.") 