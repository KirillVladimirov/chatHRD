from chathrd.parsers.base import get_file_title, process_text_blocks, remove_duplicates
from chathrd.parsers.pdf_parser import parse_pdf
from chathrd.parsers.docx_parser import parse_docx
from chathrd.parsers.xlsx_parser import parse_xlsx
from chathrd.parsers.csv_parser import parse_csv
from chathrd.parsers.txt_parser import parse_txt
from pathlib import Path

def parse_file(file_path: str) -> str:
    """Парсит файл в зависимости от его расширения."""
    file_path = Path(file_path)
    if not file_path.exists():
        return None
        
    ext = file_path.suffix.lower()
    if ext == '.pdf':
        return parse_pdf(str(file_path))
    elif ext == '.docx':
        return parse_docx(str(file_path))
    elif ext == '.xlsx':
        return parse_xlsx(str(file_path))
    elif ext == '.csv':
        return parse_csv(str(file_path))
    elif ext == '.txt':
        return parse_txt(str(file_path))
    return None

__all__ = [
    'get_file_title',
    'process_text_blocks',
    'remove_duplicates',
    'parse_file',
    'parse_pdf',
    'parse_docx',
    'parse_xlsx',
    'parse_csv',
    'parse_txt'
] 