import logging
import os
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, base_url: str = None):
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
            logger.info(f"Инициализация OllamaClient с base_url: {self.api_base}, модель: {self.model}")
        except Exception as e:
            logger.error(f"Ошибка при инициализации клиента OpenAI: {e}")
            self.client = None

    def generate_response(self, prompt: str) -> Optional[str]:
        """Генерирует ответ на запрос пользователя с использованием OpenAI API."""
        if not self.client:
            logger.error("Клиент OpenAI не был инициализирован")
            return None
            
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