import subprocess
import time
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_ollama_server():
    try:
        # Запускаем сервер Ollama
        process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Ждем пока сервер запустится
        time.sleep(5)
        
        # Скачиваем модель, если она еще не скачана
        model_name = "llama-3-8b-gpt-4o-ru1.0-gguf"
        try:
            subprocess.run(["ollama", "pull", model_name], check=True)
            logger.info(f"Model {model_name} downloaded successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to download model: {e}")
        
        logger.info("Ollama server started successfully")
        return process
    except Exception as e:
        logger.error(f"Failed to start Ollama server: {e}")
        raise

if __name__ == "__main__":
    start_ollama_server() 