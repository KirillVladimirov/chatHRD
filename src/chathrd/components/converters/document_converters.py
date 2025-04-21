"""Компоненты для конвертации документов из разных форматов."""

import logging
import tempfile
from pathlib import Path
from typing import List, Union, Dict

import fitz
from haystack import component, Document
from haystack.dataclasses import ByteStream
from pdf2image import convert_from_path
import pytesseract

logger = logging.getLogger(__name__)


@component
class OCRPDFToDocument:
    """
    Конвертирует PDF-файлы:
      – если в PDF есть текстовый слой → быстрое извлечение через PyMuPDF;
      – иначе (сканы, пустые, повреждённые) → распознавание через pytesseract.
    Выходной сокет: 'documents' (List[Document]) :contentReference[oaicite:3]{index=3}.
    """
    @component.output_types(documents=List[Document])
    def run(self, sources: List[Union[str, Path]]) -> dict:
        all_docs: List[Document] = []
        for src in sources:
            path = Path(src)
            try:
                # 1) Открываем PDF и пытаемся извлечь «сырой» текст
                pdf = fitz.open(path)  
                text_pages = [page.get_text("text", sort=True) for page in pdf]  
                full_text = "\n".join(text_pages).strip()  
                # если получилось >20 символов — считаем, что текстовый слой есть
                if len(full_text) >= 20:
                    all_docs.append(Document(
                        content=full_text,
                        meta={"name": path.name, "ocr_used": False}
                    ))
                    continue
            except Exception as e:
                logger.debug(f"PyMuPDF failed on {path.name}: {e}")
            
            # 2) PDF без текста — конвертируем страницы в изображения
            try:
                images = convert_from_path(str(path), dpi=300)
            except Exception as e:
                logger.error(f"PDF→Image conversion failed for {path.name}: {e}")
                continue

            # 3) На каждой странице запускаем Tesseract OCR
            page_texts: List[str] = []
            for i, img in enumerate(images):
                try:
                    txt = pytesseract.image_to_string(img, lang="rus+eng")
                    page_texts.append(txt)
                except Exception as exc:
                    logger.error(f"OCR failed on page {i+1} of {path.name}: {exc}")

            ocr_content = "\n".join(page_texts).strip()
            if ocr_content:
                all_docs.append(Document(
                    content=ocr_content,
                    meta={
                        "name": path.name,
                        "ocr_used": True,
                        "page_count": len(images)
                    }
                ))
            else:
                logger.warning(f"No text extracted from {path.name} even after OCR")
        return {"documents": all_docs}


@component
class PDFFastOrOCRRouter:
    """
    Разбивает источники PDF на две группы:
      – fast: файлы с текстовым слоем (PyPDFToDocument);
      – ocr : сканы и пустые (OCRPDFToDocument).
    """
    @component.output_types(fast=List[str], ocr=List[str])
    def run(self, sources: List[Union[str, Path, ByteStream]]) -> dict:
        fast, ocr = [], []
        for src in sources:
            # Подготовка пути: если ByteStream, сохраняем во временный файл
            if isinstance(src, ByteStream):
                suffix = src.metadata.get("mime_type", "").split("/")[-1] or "pdf"
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}")
                tmp.write(src.data)
                tmp.flush()
                tmp.close()
                path = Path(tmp.name)
            else:
                path = Path(src)

            # Пытаемся быстрый текстовый путь (PyMuPDF)
            try:
                pdf = fitz.open(path)
                text = "".join(page.get_text("text", sort=True) for page in pdf).strip()
                if len(text) >= 20:
                    fast.append(str(path))
                    continue
            except Exception:
                # если PyMuPDF упал — переходим к OCR
                pass

            # Во всех остальных случаях — ветка OCR
            ocr.append(str(path))

        # Возвращаем два списка путей
        return {"fast": fast, "ocr": ocr}