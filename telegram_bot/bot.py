import logging
import os
import asyncio
import sys
from typing import Final, Dict, Any, cast
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ChatAction

# Настраиваем журналирование перед импортом других модулей
# Создаем директорию для логов, если её нет
os.makedirs("logs", exist_ok=True)

# Настраиваем логирование в файл и консоль
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Проверяем, что модуль chathrd доступен
try:
    from chathrd.pipelines.querying import create_querying_pipeline, process_query
    from chathrd.config.settings import settings
    logger.info("Модуль chathrd успешно импортирован")
except ImportError as e:
    logger.error(f"Ошибка импорта модуля chathrd: {e}")
    logger.error(f"PYTHONPATH: {sys.path}")
    sys.exit(1)

# Загрузка переменных окружения
load_dotenv()
logger.info("Переменные окружения загружены")

# Константы
TELEGRAM_BOT_TOKEN: Final[str | None] = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    logger.error("Не задан токен Telegram бота. Установите переменную окружения TELEGRAM_BOT_TOKEN")
    sys.exit(1)

# Настройки API для LLM
MODEL_NAME = os.getenv("MODEL_NAME", settings.MODEL_NAME)
API_URL = os.getenv("LLM_API_URL", settings.LLM_API_URL)
if not API_URL.endswith("/v1"):
    API_URL = f"{API_URL}/v1"
PERSIST_PATH = os.getenv("CHROMA_INDEX_PATH", settings.CHROMA_INDEX_PATH)
BM25_PATH = os.getenv("BM25_INDEX_PATH", settings.BM25_INDEX_PATH)

# Проверка наличия индексов и директорий
if not Path(PERSIST_PATH).exists():
    logger.warning(f"Директория с индексом Chroma не найдена: {PERSIST_PATH}")
    
if not Path(BM25_PATH).exists():
    logger.warning(f"Файл индекса BM25 не найден: {BM25_PATH}")

logger.info(f"Конфигурация бота: MODEL_NAME={MODEL_NAME}, API_URL={API_URL}")
logger.info(f"Пути к индексам: CHROMA={PERSIST_PATH}, BM25={BM25_PATH}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение при команде /start."""
    if update.message:
        await update.message.reply_text(
            "Привет! Я бот для поиска информации в корпоративных документах. "
            "Просто задайте мне вопрос, и я постараюсь найти на него ответ."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /help."""
    if update.message:
        help_text = (
            "Я могу отвечать на вопросы по корпоративным документам. Просто напишите мне вопрос.\n\n"
            "Доступные команды:\n"
            "/start - Начать общение с ботом\n"
            "/help - Показать эту справку"
        )
        await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает входящее сообщение и отправляет запрос к пайплайну поиска."""
    if update.message and update.message.text and update.effective_chat:
        user_message = update.message.text
        user_id = update.effective_user.id if update.effective_user else "неизвестный"
        logger.info(f"Получено сообщение от пользователя {user_id}: {user_message}")
        
        # Отправляем индикацию набора текста
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )
        
        # Получение пайплайна (создаем один раз и сохраняем в контексте)
        if "pipeline" not in context.bot_data:
            try:
                logger.info(f"Создание пайплайна запросов с моделью {MODEL_NAME} и API {API_URL}")
                pipeline = create_querying_pipeline(
                    model_name=MODEL_NAME,
                    api_url=API_URL,
                    persist_path=PERSIST_PATH,
                    bm25_path=BM25_PATH
                )
                context.bot_data["pipeline"] = pipeline
                logger.info("Пайплайн запросов создан успешно")
            except Exception as e:
                logger.error(f"Ошибка при создании пайплайна: {e}")
                await update.message.reply_text(
                    "Произошла ошибка при инициализации системы поиска. Пожалуйста, попробуйте позже."
                )
                return
        
        try:
            # Запускаем обработку запроса в отдельном потоке
            pipeline = context.bot_data["pipeline"]
            logger.info(f"Отправка запроса в пайплайн: {user_message[:50]}...")
            
            # Создаем асинхронную задачу
            result_any = await asyncio.to_thread(
                process_query, 
                query=str(user_message), 
                pipeline=pipeline
            )
            
            # Приводим результат к словарю
            result = cast(Dict[str, Any], result_any)
            
            # Получаем ответ и источник
            answer = result.get("answer", "Я не смог найти ответ на ваш вопрос.")
            source = result.get("source_name", "неизвестно")
            logger.info(f"Получен ответ от источника '{source}' длиной {len(answer)} символов")
            
            # Разбиваем длинные сообщения на части, если необходимо
            if len(answer) > 4000:
                chunks = [answer[i:i+4000] for i in range(0, len(answer), 4000)]
                logger.info(f"Ответ разбит на {len(chunks)} частей")
                for i, chunk in enumerate(chunks):
                    logger.info(f"Отправка части {i+1}/{len(chunks)}")
                    await update.message.reply_text(chunk)
            else:
                await update.message.reply_text(answer)
        except Exception as e:
            logger.error(f"Ошибка при обработке запроса: {e}", exc_info=True)
            await update.message.reply_text("Извините, произошла ошибка при обработке вашего запроса.")

def main() -> None:
    """Запускает бота."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error(
            "Необходимо установить переменную окружения TELEGRAM_BOT_TOKEN"
        )
        return

    try:
        # Создание экземпляра Application
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Регистрация обработчиков
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
        )

        # Запуск бота
        logger.info(f"Запуск бота с параметрами: модель={MODEL_NAME}, API={API_URL}")
        application.run_polling()
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    logger.info("Запуск скрипта бота")
    main() 