import requests
import logging
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, base_url: str = None):
        # Используем URL из переменной окружения или значение по умолчанию
        self.base_url = base_url or os.getenv("LLM_API_URL", "http://ollama:11434")
        # Используем имя модели из переменной окружения или значение по умолчанию
        self.model = os.getenv("MODEL_NAME", "hf.co/ruslandev/llama-3-8b-gpt-4o-ru1.0-gguf:Q8_0")
        # Системный промпт для более контролируемых ответов
        self.system_prompt = """Ты помощник в диалоге с пользователем. 
Отвечай кратко и по существу на заданные вопросы.
Если пользователь просто здоровается, ответь простым приветствием без дополнительной информации."""
        logger.info(f"Инициализация OllamaClient с base_url: {self.base_url}, модель: {self.model}")

    def generate_response(self, prompt: str) -> Optional[str]:
        try:
            logger.info(f"Отправка запроса к LLM с промптом: {prompt}...")
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"{self.system_prompt}\n\nПользователь: {prompt}\n\nАссистент:",
                    "stream": False,
                    "temperature": 0.7,  # добавляем параметр температуры для контроля креативности
                    "max_tokens": 1000   # ограничиваем длину ответа
                },
                timeout=120
            )
            response.raise_for_status()
            result = response.json()["response"]
            logger.info(f"Получен ответ от LLM: {result[:100]}...")
            return result
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Ошибка соединения с LLM сервисом: {e}")
            return None
        except requests.exceptions.Timeout as e:
            logger.error(f"Тайм-аут при ожидании ответа от LLM: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при выполнении запроса к LLM: {e}")
            return None
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при генерации ответа: {e}")
            return None 