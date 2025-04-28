"""Пайплайн для обработки запросов и получения ответов."""

# pyright: reportCallIssue=false
# type: ignore[reportCallIssue]

import logging
import time
from typing import Dict, Optional

from haystack import Pipeline
from haystack.dataclasses import ChatMessage
from haystack.components.builders.chat_prompt_builder import ChatPromptBuilder
from haystack.components.routers import ConditionalRouter
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.components.joiners.document_joiner import DocumentJoiner
from haystack.components.rankers import TransformersSimilarityRanker
from haystack.utils import Secret
from haystack_integrations.document_stores.chroma import ChromaDocumentStore
from haystack_integrations.components.retrievers.chroma import ChromaQueryTextRetriever

from chathrd.components.classifiers.query_classifiers import QueryClassifierLLM, QueryDecomposerLLM
from chathrd.components.processors.document_processors import QueryCleaner
from chathrd.components.retrievers.bm25_retriever import PickledBM25Retriever
from chathrd.components.generators.multi_query_handler import MultiQueryHandler
from chathrd.components.selectors.response_selector import ResponseSelector
from chathrd.config.settings import settings

logger = logging.getLogger(__name__)


def create_querying_pipeline(
    model_name: str = "hf.co/IlyaGusev/saiga_yandexgpt_8b_gguf:Q4_0",
    api_url: str = "http://localhost:11434/v1",
    persist_path: str = "../data/chroma_index",
    bm25_path: str = "../data/bm25.pkl",
) -> Pipeline:
    """
    Создает и настраивает пайплайн для обработки запросов.
    
    Args:
        model_name: Имя модели LLM.
        api_url: URL для API LLM.
        persist_path: Путь к индексу Chroma.
        bm25_path: Путь к индексу BM25.
        
    Returns:
        Pipeline: Настроенный пайплайн для запросов.
    """
    logger.info(f"Создание пайплайна запросов с моделью: {model_name}, API: {api_url}")
    logger.info(f"Используемые индексы: Chroma: {persist_path}, BM25: {bm25_path}")

    # Настраиваем генераторы
    logger.debug("Инициализация генераторов...")
    gen_conv = OpenAIChatGenerator(
        model=model_name,
        api_key=Secret.from_token("ollama"),
        api_base_url=api_url,
        generation_kwargs={
            "temperature": settings.TEMPERATURE, 
            "max_tokens": settings.MAX_TOKENS, 
            "timeout": 240
        }
    )
    logger.debug(f"Настроен генератор диалогов с параметрами: temp={settings.TEMPERATURE}, max_tokens={settings.MAX_TOKENS}")

    gen_rag = OpenAIChatGenerator(
        model=model_name,
        api_key=Secret.from_token("ollama"),
        api_base_url=api_url,
        generation_kwargs={
            "temperature": settings.TEMPERATURE, 
            "max_tokens": settings.MAX_TOKENS, 
            "timeout": 240
        }
    )
    logger.debug("Настроен генератор RAG-ответов")

    gen_multi = OpenAIChatGenerator(
        model=model_name,
        api_key=Secret.from_token("ollama"),
        api_base_url=api_url,
        generation_kwargs={
            "temperature": settings.TEMPERATURE, 
            "max_tokens": settings.MAX_TOKENS, 
            "timeout": 240
        }
    )
    logger.debug("Настроен генератор мульти-запросов")

    # Настраиваем компоненты поиска
    logger.debug("Инициализация компонентов поиска...")
    ds = ChromaDocumentStore(persist_path=persist_path)
    logger.debug(f"Инициализировано хранилище Chroma: {persist_path}")
    
    bm25 = PickledBM25Retriever(ds, bm25_path, top_k=5)
    logger.debug(f"Инициализирован BM25 ретривер: {bm25_path}")
    
    chroma = ChromaQueryTextRetriever(document_store=ds, top_k=5)
    joiner = DocumentJoiner(join_mode="reciprocal_rank_fusion", top_k=10)
    ranker = TransformersSimilarityRanker(
        model=settings.RANKER_MODEL, 
        top_k=settings.TOP_K_RANKER
    )
    logger.debug(f"Инициализирован ранкер с моделью: {settings.RANKER_MODEL}")
    
    # Прогреваем ранкер
    logger.debug("Прогрев ранкера...")
    ranker.warm_up()
    logger.debug("Ранкер успешно прогрет")

    # PromptBuilder для простой беседы (no_search)
    logger.debug("Создание шаблонов промптов...")
    conv_pb = ChatPromptBuilder(
        template=[
            ChatMessage.from_system("Ты — дружелюбный помощник."),
            ChatMessage.from_user("{{ query }}")
        ],
        required_variables=["query"]
    )

    # PromptBuilder для RAG‑ответа (single + multi parts)
    rag_pb = ChatPromptBuilder(
        template=[
            ChatMessage.from_system("Ты — эксперт по базе знаний."),
            ChatMessage.from_user(
                "Вопрос: {{ query }}\n\n"
                "Контекст:\n{% for doc in documents %}- {{ doc.content }}\n{% endfor %}\n\n"
                "Ответь подробно и укажи источники:"
            )
        ],
        required_variables=["query", "documents"]
    )
    logger.debug("Шаблоны промптов созданы")

    # Собираем пайплайн
    logger.debug("Сборка пайплайна...")
    pipe = Pipeline()

    # 2.1 Classifier → router1
    logger.debug("Настройка компонентов классификации...")
    pipe.add_component("classifier", QueryClassifierLLM(generator=gen_conv))
    pipe.add_component("router1", ConditionalRouter(routes=[
        {"condition": "{{ need_search == false }}",
        "output": "{{ query }}", "output_name": "no_search", "output_type": str},
        {"condition": "{{ need_search == true  }}",
        "output": "{{ query }}", "output_name": "to_search", "output_type": str},
    ]))
    pipe.connect("classifier.need_search", "router1.need_search")

    # 2.2 no_search: беседа без поиска
    logger.debug("Настройка компонентов для обычной беседы...")
    pipe.add_component("conv_pb", conv_pb)
    pipe.add_component("chat_gen", gen_conv)
    pipe.connect("router1.no_search", "conv_pb.query")
    pipe.connect("conv_pb.prompt", "chat_gen.messages")

    # 2.3 to_search → декомпозиция
    logger.debug("Настройка компонентов декомпозиции запросов...")
    pipe.add_component("decomposer", QueryDecomposerLLM(generator=gen_rag))
    pipe.connect("router1.to_search", "decomposer.query")

    pipe.add_component("router2", ConditionalRouter(routes=[
        {"condition": "{{ subqueries|length > 1 }}",
        "output": "{{ subqueries }}", "output_name": "multi", "output_type": list[str]},
        {"condition": "{{ subqueries|length <= 1 }}",
        "output": "{{ subqueries[0] }}", "output_name": "single", "output_type": str},
    ]))
    pipe.connect("decomposer.subqueries", "router2.subqueries")

    # 2.4 single → поиск + генерация
    logger.debug("Настройка компонентов для одиночного запроса...")
    pipe.add_component("cleaner", QueryCleaner())
    pipe.add_component("bm25", bm25)
    pipe.add_component("chroma", chroma)
    pipe.add_component("joiner", joiner)
    pipe.add_component("ranker", ranker)
    pipe.add_component("rag_pb", rag_pb)
    pipe.add_component("rag_gen", gen_rag)

    pipe.connect("router2.single", "cleaner.query")
    pipe.connect("cleaner.query", "bm25.query")
    pipe.connect("cleaner.query", "chroma.query")
    pipe.connect("bm25.documents", "joiner.documents")
    pipe.connect("chroma.documents", "joiner.documents")
    pipe.connect("joiner.documents", "ranker.documents")

    pipe.connect("router2.single", "rag_pb.query")
    pipe.connect("ranker.documents", "rag_pb.documents")
    pipe.connect("rag_pb.prompt", "rag_gen.messages")

    # 2.5 multi → MultiQueryHandler
    logger.debug("Настройка компонентов для мульти-запросов...")
    multi_handler = MultiQueryHandler(
        bm25=bm25,
        chroma=chroma,
        joiner=pipe.get_component("joiner"),
        ranker=pipe.get_component("ranker"),
        prompt_builder=rag_pb,
        generator=gen_multi
    )
    pipe.add_component("multi_handler", multi_handler)
    pipe.connect("router2.multi", "multi_handler.multi")
    pipe.connect("router1.to_search", "multi_handler.original_query")

    # Финальный выбор ответа
    logger.debug("Настройка селектора ответов...")
    pipe.add_component("selector", ResponseSelector())

    # chat_gen — ветвь no_search
    pipe.connect("chat_gen.replies", "selector.chat_replies")

    # rag_gen — ветвь single
    pipe.connect("rag_gen.replies", "selector.rag_replies")

    # multi_handler — ветвь multi
    pipe.connect("multi_handler.answer", "selector.multi_answer")

    logger.info("Пайплайн запросов успешно собран")
    return pipe


def process_query(query: str, pipeline: Optional[Pipeline] = None) -> Dict:
    """
    Обрабатывает запрос и возвращает ответ.
    
    Args:
        query: Текст запроса.
        pipeline: Опционально - готовый пайплайн для запросов (иначе создается новый).
        
    Returns:
        Dict: Словарь с ответом.
    """
    query_length = len(query)
    logger.info(f"Обработка запроса длиной {query_length} символов: '{query[:50]}{'...' if query_length > 50 else ''}'")

    # Создаем пайплайн, если не передан
    if pipeline is None:
        logger.debug("Создание нового пайплайна...")
        pipeline = create_querying_pipeline()
    else:
        logger.debug("Используется существующий пайплайн")
    
    # Запускаем обработку запроса
    logger.debug("Запуск обработки запроса...")
    start_time = time.time()
    
    try:
        result = pipeline.run({"query": query})
        execution_time = time.time() - start_time
        
        answer_length = len(result["selector"]["answer"])
        logger.info(f"Запрос обработан за {execution_time:.2f} сек, длина ответа: {answer_length} символов")
        
        return {
            "answer": result["selector"]["answer"]
        }
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Ошибка при обработке запроса (за {execution_time:.2f} сек): {str(e)}")
        raise