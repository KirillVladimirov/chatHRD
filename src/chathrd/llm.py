"""
Модуль для работы с моделями LLM через Ollama API.
"""
import logging
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI

from chathrd.rag import get_rag_system, RAGSystem


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Client:
    """
    Клиент для взаимодействия с API Ollama для генерации текста с помощью LLM.
    Поддерживает интеграцию с RAG (Retrieval-Augmented Generation) системой.
    """
    
    def __init__(self, base_url: str = None, use_rag: bool = True, docs_dir: str = "data/parsed_files"):
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
        self.system_prompt = """Ты полезный ассистент. 
Отвечай кратко и по существу на заданные вопросы.
Отвечай только на текущий запрос пользователя.
Если пользователь просто здоровается, ответь простым приветствием без дополнительной информации."""
        
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
            
        # Инициализация RAG системы
        self.use_rag = use_rag
        self.rag_system = None
        
        if self.use_rag:
            try:
                logger.info("Инициализация RAG системы...")
                self.rag_system = get_rag_system(docs_dir=docs_dir)
                logger.info("RAG система успешно инициализирована")
            except Exception as e:
                logger.error(f"Ошибка при инициализации RAG системы: {e}")
                self.use_rag = False

    def generate_response(self, prompt: str) -> Optional[str]:
        """
        Генерирует ответ на запрос пользователя с использованием OpenAI API.
        
        При наличии RAG системы, запрос сначала обрабатывается для поиска релевантной информации,
        которая затем добавляется в контекст для LLM.
        
        Args:
            prompt: Текст запроса пользователя
            
        Returns:
            Сгенерированный ответ или None в случае ошибки
        """
        if not self.client:
            logger.error("Клиент OpenAI не был инициализирован")
            return None
        
        # Проверяем, нужно ли использовать RAG
        if self.use_rag and self.rag_system:
            try:
                # Получаем релевантные документы через RAG
                rag_results = self.rag_system.query(prompt)
                
                # Если найдены релевантные документы, используем их для улучшения ответа
                if rag_results:
                    logger.info(f"RAG нашел {len(rag_results)} релевантных документов")
                    
                    # Формируем контекст для LLM с информацией из документов
                    context_texts = []
                    for i, result in enumerate(rag_results[:3], 1):  # Ограничиваем 3 документами
                        content = result["content"]
                        source = result["meta"].get("name", "Документ без названия")
                        context_texts.append(f"Документ {i}: {content[:500]}... (Источник: {source})")
                    
                    context = "\n\n".join(context_texts)
                    
                    # Обновляем системный промпт с контекстом
                    enhanced_system_prompt = f"""Ты полезный ассистент. Используй приведенную ниже информацию для ответа на вопрос пользователя.
Старайся использовать только информацию из контекста. Если информации недостаточно, скажи что не можешь найти ответ.
Всегда указывай источники информации в конце ответа.

--- КОНТЕКСТ ---
{context}
--- КОНЕЦ КОНТЕКСТА ---

Отвечай только на текущий запрос пользователя на основе предоставленного контекста."""
                    
                    # Вызываем LLM с расширенным промптом
                    try:
                        completion = self.client.chat.completions.create(
                            model=self.model,
                            messages=[
                                {"role": "system", "content": enhanced_system_prompt},
                                {"role": "user", "content": prompt}
                            ],
                            max_tokens=1000,
                            temperature=0.7,
                        )
                        
                        result = completion.choices[0].message.content
                        logger.info(f"Получен ответ от LLM с RAG: {result[:100]}...")
                        return result
                    except Exception as e:
                        logger.error(f"Ошибка при генерации ответа с RAG: {e}")
                        # Если не удалось, пробуем обычный способ
            except Exception as e:
                logger.error(f"Ошибка при использовании RAG: {e}")
                # Если RAG не сработал, продолжаем обычным способом
            
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