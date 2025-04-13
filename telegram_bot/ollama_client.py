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
        # Устанавливаем URL напрямую для контейнера
        self.base_url = "http://llm_service:11434"
        self.model = "hf.co/ruslandev/llama-3-8b-gpt-4o-ru1.0-gguf:Q8_0"
        logger.info(f"Initializing OllamaClient with base_url: {self.base_url}")

    def generate_response(self, prompt: str) -> Optional[str]:
        try:
            logger.info(f"Sending request to LLM with prompt: {prompt}")
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )
            response.raise_for_status()
            result = response.json()["response"]
            logger.info(f"Received response from LLM: {result[:100]}...")
            return result
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to LLM service: {e}")
            return None
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout while waiting for LLM response: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to LLM: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating response: {e}")
            return None 