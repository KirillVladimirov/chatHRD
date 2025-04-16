import fitz
import pytesseract
from PIL import Image
from chathrd.parsers.utils import process_text_blocks, remove_duplicates, logger

def extract_text_with_ocr(page) -> str:
    """Извлекает текст из страницы PDF с помощью OCR."""
    try:
        # Получаем изображение страницы
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Применяем OCR
        text = pytesseract.image_to_string(img, lang='rus+eng')
        return text
    except Exception as e:
        logger.error(f"Ошибка при OCR: {str(e)}")
        return ""

def parse_pdf(file_path: str) -> str:
    """Парсит PDF файл и возвращает его содержимое в markdown формате."""
    try:
        pdf = fitz.open(file_path)
        content = []
        current_page = 1

        for page in pdf:
            # Сначала пробуем извлечь текст обычным способом
            text = page.get_text()
            
            # Если текст пустой, пробуем OCR
            if not text.strip():
                text = extract_text_with_ocr(page)
                if not text.strip():
                    continue
                    
            content.append(f"\n## Страница {current_page}\n")
            current_page += 1
            
            blocks = text.split('\n\n')
            processed_blocks = []
            for block in blocks:
                if not block.strip() or block.strip().isdigit():
                    continue
                lines = block.split('\n')
                processed_lines = remove_duplicates(lines)
                processed_block = '\n'.join(processed_lines).strip()
                if processed_block:
                    processed_blocks.append(processed_block)
            
            content.append(process_text_blocks(processed_blocks))
        
        pdf.close()
        return '\n'.join(content)
    except Exception as e:
        logger.error(f"Ошибка при парсинге PDF файла {file_path}: {str(e)}")
        return f"Ошибка при обработке PDF файла: {str(e)}" 