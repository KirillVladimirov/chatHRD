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
)

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


async def start(update: Update, context: CallbackContext) -> None:
    """Отправляет приветственное сообщение при команде /start."""
    if update.message:
        await update.message.reply_text(
            "Привет! Я эхо-бот. Отправь мне сообщение, и я его повторю."
        )


async def echo(update: Update, context: CallbackContext) -> None:
    """Повторяет полученное текстовое сообщение."""
    if update.message and update.message.text:
        logger.info(f"Получено сообщение от пользователя: {update.message.text}")
        await update.message.reply_text(update.message.text)


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
        MessageHandler(filters.TEXT & ~filters.COMMAND, echo)
    )

    # Запуск бота
    logger.info("Запуск бота...")
    application.run_polling()


if __name__ == "__main__":
    main() 