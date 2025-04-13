import logging
import os
from typing import Final

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from ollama_client import OllamaClient

# Загрузка переменных окружения
load_dotenv()

# Константы
TELEGRAM_BOT_TOKEN: Final[str | None] = os.getenv("TELEGRAM_BOT_TOKEN")

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Инициализация клиента Ollama
ollama_client = OllamaClient()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение при команде /start."""
    if update.message:
        await update.message.reply_text(
            "Привет! Я бот с интегрированной моделью Llama. Отправьте мне сообщение, и я отвечу."
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает входящее сообщение и отправляет запрос в LLM."""
    if update.message and update.message.text:
        user_message = update.message.text
        logger.info(f"Получено сообщение от пользователя: {user_message}")
        
        # Отправляем сообщение в LLM
        llm_response = ollama_client.generate_response(user_message)
        
        if llm_response:
            await update.message.reply_text(llm_response)
        else:
            await update.message.reply_text("Извините, произошла ошибка при обработке вашего сообщения.")

def main() -> None:
    """Запускает бота."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error(
            "Необходимо установить переменную окружения TELEGRAM_BOT_TOKEN"
        )
        return

    # Создание экземпляра Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Запуск бота
    logger.info("Запуск бота...")
    application.run_polling()


if __name__ == "__main__":
    main() 