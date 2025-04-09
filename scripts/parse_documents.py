#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from pathlib import Path
from chathrd import parse_file

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_files_from_list(files: list, output_dir: str):
    """
    Парсит файлы из списка и сохраняет результаты в markdown формате.
    
    Args:
        files: Список файлов для парсинга
        output_dir: Директория для сохранения результатов
    """
    # Создаем директорию для результатов, если она не существует
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Парсим каждый файл
    for file_name in files:
        file_path = Path("data/downloaded_files") / file_name
        if not file_path.exists():
            logger.warning(f"Файл не найден: {file_path}")
            continue
            
        try:
            # Парсим файл
            content = parse_file(str(file_path))
            
            # Сохраняем результат
            output_file = output_path / f"{file_path.stem}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"Успешно обработан файл: {file_path}")
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {file_path}: {e}")

if __name__ == "__main__":
    # Список файлов для парсинга
    files = [
        # PDF файлы - документация и инструкции
        "zid_50_cat.pdf",
        "Конспект с таймкодами. Знакомство с функциями и массивами.pdf",
        "VK_HR_Tek_-_Описание_API_Документация_по_API_07.03.2024.pdf",
        "Чек-лист_бадди_для_новых_сотрудников_VK_Tech.pdf",
        "Легенда_к_макету_стартовой_страницы_03-06-2024.pdf",
        "Руководство по использованию Vaultwarden - InfoSec - Confluence.pdf",
        # PDF файлы - учебники и книги
        "Фролов_К_В_Горные_машины_МЭ,_том_IV_24_2010.pdf",
        "Фролов_К_В_Двигатели_внутреннего_сгорания_МЭ,_том_IV_14_2013.pdf",
        "Фролов_К_В_Авиационные_двигатели_МЭ,_том_IV_21,_книга_3_2010.pdf",
        "Фролов_К_В_Динамика_и_прочность_машин_МЭ,_том_I_3,_книга_1_1994.pdf",
        "Ольга_Назина_Что_такое_тестирование.pdf",
        "Software_Testing_-_Base_Course_Svyatoslav_Kulikov_-_3rd_edition_-_RU_1.pdf",
        # PDF файлы - энциклопедии
        "05_Великие_музеи_мира_Метрополитен_2011.pdf",
        "06_Великие_музеи_мира_Эрмитаж_Часть_1_2011.pdf",
        "04_Великие_музеи_мира_Египетский_музей_2011.pdf",
        # DOCX файлы - инструкции и документация
        "Инструкция работника для подачи заявления на социальные льготы.docx",
        "Скриншоты текущего Sap_ модуль компетенций и СБГ213412412412412412 цаываывавыаыа.docx",
        "Черновик.docx",
        # XLSX файлы - таблицы с данными
        "employees.xlsx",
        "ideas_admins_list.xlsx",
        "events_admins_list.xlsx",
        "top.xlsx",
        "authors.xlsx",
        "Шаблон_загрузки_подразделений.xlsx",
        "Чек_лист_проверок__Редактирование_разрешений_сервиса_Списки.xlsx",
        # XLSX файлы - тестовые данные
        "MOCK_DATA.xlsx",
        "MOCK_DATA-2.xlsx",
        "MOCK_DATA-3.xlsx",
        # XLSX файлы - шаблоны
        "Экспорт_участников_регистрации.xlsx",
        "Шаблон загрузки организации новый.xlsx",
    ]
    
    # Директория для результатов
    output_dir = "data/parsed_files"
    
    parse_files_from_list(files, output_dir) 