import os
import logging
from typing import List

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