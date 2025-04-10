FROM python:3.10-slim

# Установка системных зависимостей, если они нужны боту
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     package1 package2 \
#     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем файлы управления зависимостями и README
COPY pyproject.toml ./
COPY README.md ./
# COPY hatch.toml ./ # Раскомментируйте, если используете hatch.toml

# Копируем основной исходный код приложения
COPY ./src /app/src

# Устанавливаем зависимости проекта И САМ ПРОЕКТ (включая бота и dev)
# Используем --no-cache-dir для уменьшения размера образа
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ".[dev]" # Устанавливаем сам пакет chathrd, его основные и dev зависимости

# Копируем код бота в образ (после установки зависимостей)
COPY ./telegram_bot /app/telegram_bot

# Команда для запуска бота
CMD ["python", "telegram_bot/bot.py"] 