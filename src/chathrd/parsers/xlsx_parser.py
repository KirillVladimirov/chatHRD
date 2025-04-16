import pandas as pd
from tabulate import tabulate
from chathrd.parsers.utils import get_file_title, logger

def parse_xlsx(file_path: str) -> str:
    """Парсит XLSX файл и возвращает его содержимое в markdown формате."""
    try:
        content = [f"# {get_file_title(file_path)}", ""]
        
        # Читаем Excel файл
        xls = pd.ExcelFile(file_path)
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            df = df.dropna(axis=0, how='all').dropna(axis=1, how='all')
            
            if not df.empty:
                content.extend([
                    f"### Лист: {sheet_name}",
                    "",
                    tabulate(df, headers='keys', tablefmt='pipe', showindex=False),
                    ""
                ])
            else:
                content.extend([
                    f"### Лист: {sheet_name}",
                    "",
                    "(пустой)",
                    ""
                ])
        
        return '\n'.join(content)
    except Exception as e:
        logger.error(f"Ошибка при парсинге XLSX файла {file_path}: {str(e)}")
        return f"Ошибка при обработке XLSX файла: {str(e)}" 