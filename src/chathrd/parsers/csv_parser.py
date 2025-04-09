import pandas as pd
from tabulate import tabulate
from .base import get_file_title, logger

def parse_csv(file_path: str) -> str:
    """Парсит CSV файл и возвращает его содержимое в markdown формате."""
    try:
        content = [f"# {get_file_title(file_path)}", ""]
        
        # Читаем CSV файл
        df = pd.read_csv(file_path)
        df = df.dropna(axis=0, how='all').dropna(axis=1, how='all')
        
        if not df.empty:
            content.extend([
                tabulate(df, headers='keys', tablefmt='pipe', showindex=False),
                ""
            ])
        else:
            content.extend([
                "(пустой)",
                ""
            ])
        
        return '\n'.join(content)
    except Exception as e:
        logger.error(f"Ошибка при парсинге CSV файла {file_path}: {str(e)}")
        return f"Ошибка при обработке CSV файла: {str(e)}" 