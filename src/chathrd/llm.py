"""
Модуль для работы с моделями LLM через Ollama API.
"""
import logging
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

from chathrd.pipelines.querying import create_querying_pipeline, process_query


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Client:
    """
    Клиент для взаимодействия с API Ollama для генерации текста с помощью LLM.
    Поддерживает интеграцию с RAG (Retrieval-Augmented Generation) системой через современные пайплайны.
    """
    
    def __init__(self, base_url: Optional[str] = None, use_rag: bool = True, docs_dir: str = "data/parsed_files"):
        """
        Инициализирует клиент для работы с Ollama API.
        
        Args:
            base_url: Базовый URL для API Ollama (если None, берется из переменной окружения LLM_API_URL)
            use_rag: Использовать ли RAG систему для улучшения ответов
            docs_dir: Директория с документами для RAG (по умолчанию "data/parsed_files")
        """
        # Используем URL из переменной окружения или значение по умолчанию
        self.base_url = base_url or os.getenv("LLM_API_URL", "http://ollama:11434")
        # OpenAI-совместимый URL (добавляем /v1 к базовому URL)
        self.api_base = f"{self.base_url}/v1"
        # Используем имя модели из переменной окружения или значение по умолчанию
        self.model = os.getenv("MODEL_NAME", "hf.co/ruslandev/llama-3-8b-gpt-4o-ru1.0-gguf:Q8_0")
        # Системный промпт для более контролируемых ответов
        self.system_prompt = "Ты полезный ассистент. Отвечай кратко и по существу на заданные вопросы. Отвечай только на текущий запрос пользователя. Всегда отвечай на русском языке. Если пользователь просто здоровается, ответь простым приветствием без дополнительной информации."
        
        # Инициализация клиента OpenAI
        try:
            self.client = OpenAI(
                base_url=self.api_base,
                api_key="ollama"  # API ключ не используется Ollama, но требуется библиотекой
            )
            logger.info(f"Инициализация Client с base_url: {self.api_base}, модель: {self.model}")
        except Exception as e:
            logger.error(f"Ошибка при инициализации клиента OpenAI: {e}")
            self.client = None
            
        # Инициализация RAG пайплайна
        self.use_rag = use_rag
        self.querying_pipeline = None
        
        if self.use_rag:
            try:
                logger.info("Инициализация пайплайна запросов...")
                self.querying_pipeline = create_querying_pipeline(
                    model_name=self.model,
                    api_url=self.api_base,
                    persist_path=os.path.join(os.path.dirname(docs_dir), "chroma_index"),
                    bm25_path=os.path.join(os.path.dirname(docs_dir), "bm25.pkl"),
                )
                logger.info("Пайплайн запросов успешно инициализирован")
            except Exception as e:
                logger.error(f"Ошибка при инициализации пайплайна запросов: {e}")
                self.use_rag = False

    def generate_response(self, prompt: str) -> Optional[str]:
        """
        Генерирует ответ на запрос пользователя с использованием OpenAI API.
        
        При наличии RAG системы, запрос сначала обрабатывается через пайплайн запросов,
        который автоматически выполняет поиск по индексам и формирует контекстуальный ответ.
        
        Args:
            prompt: Текст запроса пользователя
            
        Returns:
            Сгенерированный ответ или None в случае ошибки
        """
        if not self.client:
            logger.error("Клиент OpenAI не был инициализирован")
            return None
        
        # Проверяем, нужно ли использовать RAG
        if self.use_rag and self.querying_pipeline:
            try:
                # Обрабатываем запрос через пайплайн запросов
                result = process_query(prompt, self.querying_pipeline)
                if result and isinstance(result, Dict) and "answer" in result:
                    answer = result["answer"]
                    source = result.get("source_name", "пайплайн запросов")
                    logger.info(f"Получен ответ от {source}: {answer[:100]}...")
                    return answer
            except Exception as e:
                logger.error(f"Ошибка при использовании пайплайна запросов: {e}")
                # Если пайплайн не сработал, продолжаем обычным способом
        
        # Стандартная генерация без RAG
        try:
            logger.info(f"Отправка запроса к LLM с промптом: {prompt}...")
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7,
            )
            
            result = completion.choices[0].message.content
            logger.info(f"Получен ответ от LLM: {result[:100]}...")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {e}")
            return None 