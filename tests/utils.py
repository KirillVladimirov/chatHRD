import fitz
from docx import Document
import pandas as pd
from pathlib import Path
from tests.constants import TEST_FILES_DIR

def create_pdf_file(path: Path, text: str) -> None:
    """Создает PDF файл с заданным текстом."""
    doc = fitz.open()
    page = doc.new_page()
    if text:
        # Разбиваем текст на строки и вставляем каждую строку
        y = 72
        for line in text.split('\n'):
            page.insert_text((50, y), line, fontsize=12, color=(0, 0, 0))
            y += 20
    doc.save(path)
    doc.close()

def create_docx_file(path: Path, text: str) -> None:
    """Создает DOCX файл с заданным текстом."""
    doc = Document()
    if text:
        doc.add_paragraph(text)
    doc.save(path)

def create_xlsx_file(path: Path, data: dict) -> None:
    """Создает XLSX файл с заданными данными."""
    if data:
        df = pd.DataFrame(data)
        df.to_excel(path, index=False)
    else:
        pd.DataFrame().to_excel(path, index=False)

def create_csv_file(path: Path, data: dict) -> None:
    """Создает CSV файл с заданными данными."""
    if data:
        df = pd.DataFrame(data)
        df.to_csv(path, index=False)
    else:
        pd.DataFrame().to_csv(path, index=False)

def create_txt_file(path: Path, text: str) -> None:
    """Создает TXT файл с заданным текстом."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def cleanup_test_files() -> None:
    """Удаляет все тестовые файлы."""
    for file_path in TEST_FILES_DIR.glob("*"):
        file_path.unlink()
    if TEST_FILES_DIR.exists():
        TEST_FILES_DIR.rmdir() 