import os
import subprocess
from pathlib import Path
from chathrd.parsers.utils import logger

def parse_doc(file_path: str) -> str:
    """
    Извлекает текст из файла .doc с помощью antiword и форматирует его в Markdown.
    
    Args:
        file_path: Путь к файлу .doc
    
    Returns:
        Извлеченный текст в формате Markdown
    """
    logger.info(f"Обработка DOC файла: {file_path}")
    
    # Проверяем существование файла
    if not os.path.exists(file_path):
        logger.error(f"Файл не найден: {file_path}")
        return f"Ошибка: файл {file_path} не найден"
    
    try:
        # Получаем имя файла для заголовка
        file_name = Path(file_path).stem
        
        # Используем antiword для извлечения текста
        result = subprocess.run(
            ["antiword", file_path], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # Получаем текст из результата
        text = result.stdout
        
        if not text or text.isspace():
            logger.warning(f"Файл {file_path} не содержит текста или не может быть обработан")
            return f"# {file_name}\n\nФайл не содержит текста или не может быть обработан antiword."
        
        # Форматируем текст в Markdown
        markdown_text = f"# {file_name}\n\n{text}"
        
        logger.info(f"DOC файл успешно обработан: {file_path}")
        return markdown_text
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при обработке DOC файла {file_path}: {e}")
        return f"Ошибка при обработке файла {file_path} с помощью antiword: {e}"
    
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при обработке DOC файла {file_path}: {e}")
        return f"Непредвиденная ошибка при обработке файла {file_path}: {e}" 