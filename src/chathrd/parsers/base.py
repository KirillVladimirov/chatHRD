from typing import Union
from pathlib import Path

# Импорт общих утилит из utils
from chathrd.parsers.utils import logger

# Импорты парсеров
from chathrd.parsers.pdf_parser import parse_pdf
from chathrd.parsers.docx_parser import parse_docx
from chathrd.parsers.doc_parser import parse_doc
from chathrd.parsers.xlsx_parser import parse_xlsx
from chathrd.parsers.csv_parser import parse_csv
from chathrd.parsers.txt_parser import parse_txt

def parse_file(file_path: Union[str, Path]) -> str:
    """
    Parse a file based on its extension.

    Arguments:
        file_path {str or Path} -- The path to the file to parse.

    Returns:
        str -- The content of the file in markdown format.
    """
    file_path = Path(file_path)
    file_extension = file_path.suffix.lower()
    
    try:
        if file_extension == '.pdf':
            return parse_pdf(str(file_path))
        elif file_extension == '.docx':
            return parse_docx(str(file_path))
        elif file_extension == '.doc':
            return parse_doc(str(file_path))
        elif file_extension == '.xlsx':
            return parse_xlsx(str(file_path))
        elif file_extension == '.csv':
            return parse_csv(str(file_path))
        elif file_extension == '.txt':
            return parse_txt(str(file_path))
        else:
            logger.warning(f"Неподдерживаемый формат файла: {file_extension} для {file_path}")
            return f"Неподдерживаемый формат файла: {file_extension}"
    except Exception as e:
        logger.error(f"Ошибка при обработке файла {file_path}: {e}")
        return f"Ошибка при обработке файла: {e}" 