"""Пайплайн для индексации документов."""

# pyright: reportCallIssue=false
# type: ignore[reportCallIssue]

import os
import logging
import time
from pathlib import Path
from typing import List, Optional

from haystack import Pipeline
from haystack.components.routers import FileTypeRouter
from haystack.components.converters import (
    TextFileToDocument, 
    PyPDFToDocument,
    DOCXToDocument,
    CSVToDocument,
    XLSXToDocument,
    MarkdownToDocument,
    TikaDocumentConverter
)
from haystack.components.joiners.document_joiner import DocumentJoiner
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.components.writers import DocumentWriter
from haystack_integrations.document_stores.chroma import ChromaDocumentStore

from chathrd.components.converters.document_converters import OCRPDFToDocument, PDFFastOrOCRRouter
from chathrd.components.processors.document_processors import OverlapToStr, EncodingSplitter
from chathrd.components.retrievers.bm25_retriever import BM25Builder
from chathrd.config.settings import settings

logger = logging.getLogger(__name__)


def create_indexing_pipeline(persist_path: str = "../data/chroma_index") -> Pipeline:
    """
    Создает и настраивает пайплайн для индексации документов.
    
    Args:
        persist_path: Путь для сохранения индекса Chroma.
        
    Returns:
        Pipeline: Настроенный пайплайн для индексации.
    """
    logger.info(f"Создание пайплайна индексации с хранилищем по пути: {persist_path}")
    
    # Инициализация хранилища (Chroma) с сохранением на диск
    embedding_store = ChromaDocumentStore(persist_path=persist_path)
    logger.debug("Инициализировано хранилище Chroma")

    # Инициализация компонентов
    logger.debug("Инициализация компонентов пайплайна...")
    file_router = FileTypeRouter(
        mime_types=[
            "text/plain",                        # .txt, .yml
            "text/csv",                          # .csv
            "text/markdown",                     # .md
            "application/json",                  # .json
            "application/pdf",                   # .pdf
            "application/msword",                # .doc
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
            "application/epub+zip",              # .epub
            "application/vnd.ms-excel",          # .xls
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",        # .xlsx
        ]
    )
    logger.debug("Создан маршрутизатор файлов по MIME-типам")
    # --- конвертеры ---
    txt_utf8 = TextFileToDocument()                 # encoding="utf-8" по умолчанию
    txt_cp = TextFileToDocument(encoding="cp1251")  # второй конвертер под Windows‑1251
    csv_converter = CSVToDocument()
    json_converter = TextFileToDocument()  # просто читаем json файлы как текст
    
    tika_doc_converter = TikaDocumentConverter()   # .doc
    tika_epub_converter = TikaDocumentConverter()  # .epub
    tika_xls_converter = TikaDocumentConverter()   # .xls
    docx_converter = DOCXToDocument()
    xlsx_converter = XLSXToDocument(table_format="markdown")
    tika_unclassified_converter = TikaDocumentConverter()   # for all other
    md_converter = MarkdownToDocument()

    # --- объединитель ---
    joiner = DocumentJoiner(join_mode="concatenate")

    # --- процессоры ---
    cleaner = DocumentCleaner(
        remove_empty_lines=True,
        remove_extra_whitespaces=True,
        remove_repeated_substrings=True, 
    )
    splitter = DocumentSplitter(
        split_by="word",
        split_length=settings.MAX_SPLIT_LENGTH, 
        split_overlap=settings.SPLIT_OVERLAP
    )
    
    # --- эмбеддеры ---
    embedder = SentenceTransformersDocumentEmbedder(
        settings.EMBEDDER_MODEL
    )
    embedding_writer = DocumentWriter(document_store=embedding_store)

    # --- модифицированные компоненты ---
    overlap_fix = OverlapToStr()
    enc_split = EncodingSplitter()

    # Инициализируем конвертеры для PDF
    pdf_router = PDFFastOrOCRRouter()
    pdf_fast = PyPDFToDocument()
    ocr_pdf = OCRPDFToDocument()

    # BM25 индексатор
    bm25_builder = BM25Builder()

    # Построение пайплайна
    indexing_pipeline = Pipeline()
    logger.debug("Создан пустой пайплайн, добавление компонентов...")

    # Добавляем компоненты
    indexing_pipeline.add_component("router", file_router)
    indexing_pipeline.add_component("enc_split", enc_split)
    indexing_pipeline.add_component("txt_utf8", txt_utf8)
    indexing_pipeline.add_component("txt_cp", txt_cp)
    indexing_pipeline.add_component("md_converter", md_converter)
    indexing_pipeline.add_component("csv_converter", csv_converter)
    indexing_pipeline.add_component("json_converter", json_converter)
    
    indexing_pipeline.add_component("pdf_router", pdf_router)
    indexing_pipeline.add_component("pdf_fast", pdf_fast)
    indexing_pipeline.add_component("ocr_pdf", ocr_pdf)

    indexing_pipeline.add_component("docx_converter", docx_converter)
    indexing_pipeline.add_component("xlsx_converter", xlsx_converter)
    indexing_pipeline.add_component("tika_doc_converter", tika_doc_converter)
    indexing_pipeline.add_component("tika_epub_converter", tika_epub_converter)
    indexing_pipeline.add_component("tika_xls_converter", tika_xls_converter)
    indexing_pipeline.add_component("tika_unclassified_converter", tika_unclassified_converter)

    indexing_pipeline.add_component("join", joiner)
    indexing_pipeline.add_component("cleaner", cleaner)
    indexing_pipeline.add_component("splitter", splitter)
    indexing_pipeline.add_component("overlap_fix", overlap_fix)
    indexing_pipeline.add_component("embedder", embedder)
    indexing_pipeline.add_component("bm25_builder", bm25_builder)
    indexing_pipeline.add_component("embedding_writer", embedding_writer)

    # ───────── Router → Converters ─────────
    logger.debug("Настройка соединений между компонентами...")
    # 1. текстовые файлы сначала идут в детектор
    indexing_pipeline.connect("router.text/plain", "enc_split.sources")
    # 2. две ветки на разные конвертеры
    indexing_pipeline.connect("enc_split.utf8", "txt_utf8.sources")
    indexing_pipeline.connect("enc_split.cp", "txt_cp.sources")
    
    indexing_pipeline.connect("router.text/csv", "csv_converter.sources")     # .csv
    indexing_pipeline.connect("router.text/markdown", "md_converter.sources")    # .md
    indexing_pipeline.connect("router.application/json", "json_converter.sources")  # .json

    # PDF идут в роутер
    indexing_pipeline.connect("router.application/pdf", "pdf_router.sources")
    #    → «быстрые» PDF → PyPDFToDocument
    indexing_pipeline.connect("pdf_router.fast", "pdf_fast.sources")
    #    → «сканы» и пустые → OCRPDFToDocument
    indexing_pipeline.connect("pdf_router.ocr", "ocr_pdf.sources")

    # Office / EPUB / XLS — универсальный Tika
    indexing_pipeline.connect("router.application/msword",
                    "tika_doc_converter.sources")                          # .doc
    indexing_pipeline.connect("router.application/epub+zip",
                    "tika_epub_converter.sources")                          # .epub
    indexing_pipeline.connect("router.application/vnd.ms-excel",
                    "tika_xls_converter.sources")                          # .xls

    # DOCX и XLSX — узкоспециализированные конвертеры
    indexing_pipeline.connect("router.application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "docx_converter.sources")                          # .docx
    indexing_pipeline.connect("router.application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "xlsx_converter.sources")                          # .xlsx

    # Всё, что не распознано (или не перечислено)  →  Tika‑fallback
    indexing_pipeline.connect("router.unclassified", "tika_unclassified_converter.sources")


    # Подключаем каждый конвертер → joiner
    # 3. оба конвертера → DocumentJoiner
    indexing_pipeline.connect("txt_utf8.documents", "join.documents")
    indexing_pipeline.connect("txt_cp.documents", "join.documents")
    indexing_pipeline.connect("csv_converter.documents", "join.documents")    # .csv
    indexing_pipeline.connect("md_converter.documents", "join.documents")     # .csv
    indexing_pipeline.connect("json_converter.documents", "join.documents")   # .json
    
    indexing_pipeline.connect("pdf_fast.documents", "join.documents")
    indexing_pipeline.connect("ocr_pdf.documents", "join.documents")
    indexing_pipeline.connect("docx_converter.documents", "join.documents")   # .docx
    indexing_pipeline.connect("xlsx_converter.documents", "join.documents")   # .xlsx
    indexing_pipeline.connect("tika_doc_converter.documents", "join.documents")   # .doc
    indexing_pipeline.connect("tika_epub_converter.documents", "join.documents")   # .epub
    indexing_pipeline.connect("tika_xls_converter.documents", "join.documents")   # .xls
    indexing_pipeline.connect("tika_unclassified_converter.documents", "join.documents")   # неопределенные


    # Остальная цепочка принимает ОДИН поток документов
    indexing_pipeline.connect("join.documents", "cleaner.documents")
    indexing_pipeline.connect("cleaner.documents", "splitter.documents")
    indexing_pipeline.connect("splitter.documents", "overlap_fix.documents")
    indexing_pipeline.connect("overlap_fix.documents", "embedder.documents")
    indexing_pipeline.connect("embedder.documents", "bm25_builder.documents")
    indexing_pipeline.connect("bm25_builder.documents", "embedding_writer.documents")
    
    logger.info("Пайплайн индексации успешно создан и настроен")
    return indexing_pipeline


def run_indexing(file_paths: Optional[List[str]] = None, data_dir: str = "../data/downloaded_files"):
    """
    Запускает индексацию для указанных файлов или всех файлов в каталоге.
    
    Args:
        file_paths: Список путей к файлам для индексации.
        data_dir: Директория с файлами (если file_paths не указан).
    """
    logger.info(f"Запуск индексации, указано файлов: {len(file_paths) if file_paths else 0}")
    
    if not file_paths:
        # Если пути не указаны, берем все файлы из директории
        logger.info(f"Поиск файлов в директории: {data_dir}")
        file_paths = [os.path.join(data_dir, name) for name in os.listdir(data_dir)]
        logger.info(f"Найдено файлов: {len(file_paths)}")
    
    # Проверяем, что файлы существуют
    existing_files = [path for path in file_paths if os.path.exists(path)]
    
    if len(existing_files) != len(file_paths):
        missing_count = len(file_paths) - len(existing_files)
        logger.warning(f"Пропущено {missing_count} несуществующих файлов")
        
        # Выводим список отсутствующих файлов
        missing_files = [path for path in file_paths if not os.path.exists(path)]
        for path in missing_files[:5]:  # Ограничиваем список первыми 5 файлами
            logger.warning(f"Файл не найден: {path}")
        if len(missing_files) > 5:
            logger.warning(f"...и еще {len(missing_files) - 5} файлов")
    
    if not existing_files:
        logger.error("Нет файлов для индексации")
        return
    
    # Выводим статистику по файлам
    logger.info(f"Начинаем индексацию {len(existing_files)} файлов")
    
    # Выводим информацию о размерах файлов
    total_size = sum(os.path.getsize(path) for path in existing_files)
    avg_size = total_size / len(existing_files) if existing_files else 0
    logger.info(f"Общий размер файлов: {total_size/1024/1024:.2f} МБ, средний размер: {avg_size/1024:.2f} КБ")
    
    # Создаем и запускаем пайплайн
    logger.info("Создание пайплайна индексации...")
    pipeline = create_indexing_pipeline()
    
    logger.info("Запуск процесса индексации...")
    start_time = time.time()
    
    try:
        pipeline.run({"router": {"sources": existing_files}})
        
        # Вычисляем время выполнения
        execution_time = time.time() - start_time
        logger.info(f"Индексация завершена успешно. Проиндексировано {len(existing_files)} файлов за {execution_time:.2f} сек " 
                    f"({execution_time/len(existing_files):.2f} сек/файл)")
        
    except Exception as e:
        logger.error(f"Ошибка при индексации файлов: {str(e)}")
        raise 