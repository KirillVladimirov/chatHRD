from chathrd.parsers.utils import get_file_title, logger

def parse_txt(file_path: str) -> str:
    """Парсит TXT файл и возвращает его содержимое в markdown формате."""
    try:
        content = [f"# {get_file_title(file_path)}", ""]
        
        # Читаем TXT файл
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read().strip()
            
        if text:
            content.extend([
                text,
                ""
            ])
        else:
            content.extend([
                "(пустой)",
                ""
            ])
        
        return '\n'.join(content)
    except Exception as e:
        logger.error(f"Ошибка при парсинге TXT файла {file_path}: {str(e)}")
        return f"Ошибка при обработке TXT файла: {str(e)}" 