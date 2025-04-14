import os
import logging
from typing import List, Optional, Dict, Callable, Any
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_file_title(file_path: str) -> str:
    """
    Получает заголовок файла из его имени.
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        Имя файла без пути
    """
    return os.path.basename(file_path)

def process_text_blocks(blocks: List[str]) -> str:
    """
    Обрабатывает блоки текста, объединяя их в параграфы.
    
    Args:
        blocks: Список блоков текста для обработки
        
    Returns:
        Обработанный текст с правильной структурой параграфов
    """
    if not blocks:
        return ""
        
    processed_blocks = []
    for block in blocks:
        if not block.strip():
            continue
            
        lines = block.split('\n')
        processed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Пропуск пустых строк
            if not line:
                i += 1
                continue
                
            # Обработка заголовков
            if line.startswith(('###', '##')):
                processed_lines.append('\n' + line + '\n')
                i += 1
                continue
                
            # Обработка обычного текста
            sentence = line
            while i + 1 < len(lines) and not lines[i + 1].strip().startswith(('###', '##')):
                next_line = lines[i + 1].strip()
                if not next_line:
                    break
                    
                if sentence.endswith('-'):  # Перенос слова
                    sentence = sentence[:-1] + next_line
                elif any(sentence.endswith(p) for p in '.!?'):  # Конец предложения
                    processed_lines.append(sentence)
                    sentence = next_line
                else:  # Продолжение предложения
                    sentence += ' ' + next_line
                    
                i += 1
                
            if sentence:
                processed_lines.append(sentence)
                
            i += 1
            
        processed_blocks.append('\n'.join(processed_lines))
        
    return '\n\n'.join(processed_blocks)

def remove_duplicates(lines: List[str]) -> List[str]:
    """
    Удаляет дубликаты строк, сохраняя порядок.
    
    Args:
        lines: Список строк, возможно содержащий дубликаты
        
    Returns:
        Список строк без дубликатов, с сохранением исходного порядка
    """
    if not lines:
        return []
        
    seen = set()
    return [line for line in lines if not (line in seen or seen.add(line))]

def parse_file(file_path: str) -> Optional[str]:
    """
    Парсит файл в зависимости от его расширения.
    
    Поддерживаемые форматы:
    - PDF (.pdf) - через PyMuPDF и OCR при необходимости
    - Word (.docx) - через python-docx
    - Excel (.xlsx) - через pandas
    - CSV (.csv) - через pandas
    - Текст (.txt) - обычное чтение
    
    Args:
        file_path: Путь к файлу для парсинга
        
    Returns:
        Извлеченный текст в формате Markdown или None, если файл не поддерживается или произошла ошибка
    """
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"Файл не существует: {file_path}")
            return None
            
        if not file_path.is_file():
            logger.error(f"Указанный путь не является файлом: {file_path}")
            return None
            
        # Словарь с функциями парсинга для каждого расширения
        parsers: Dict[str, Callable[[str], Optional[str]]] = {}
        
        # Определяем расширение файла
        ext = file_path.suffix.lower()
        
        # Динамический импорт только нужного парсера
        if ext == '.pdf':
            from chathrd.parsers.pdf_parser import parse_pdf
            return parse_pdf(str(file_path))
        elif ext == '.docx':
            from chathrd.parsers.docx_parser import parse_docx
            return parse_docx(str(file_path))
        elif ext == '.xlsx':
            from chathrd.parsers.xlsx_parser import parse_xlsx
            return parse_xlsx(str(file_path))
        elif ext == '.csv':
            from chathrd.parsers.csv_parser import parse_csv
            return parse_csv(str(file_path))
        elif ext == '.txt':
            from chathrd.parsers.txt_parser import parse_txt
            return parse_txt(str(file_path))
        else:
            logger.warning(f"Неподдерживаемый формат файла: {ext} для {file_path}")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка при парсинге файла {file_path}: {e}")
        return None 