FROM python:3.11-slim

# Установка необходимых инструментов
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    make \
    gnupg2 \
    lsb-release \
    graphviz \
    antiword \
    unrtf \
    pandoc \
    tesseract-ocr \
    tesseract-ocr-rus \
    && echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
    && apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client-16 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем файлы управления зависимостями и README
COPY pyproject.toml ./
COPY README.md ./
COPY Makefile ./
COPY .env ./

# Копируем основной исходный код приложения
COPY src /app/src
COPY scripts /app/scripts

# Устанавливаем зависимости проекта
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ".[dev]" && \
    pip install -e .

# Установка openai
RUN pip install openai>=1.0.0

# Копируем код бота и скрипты
COPY telegram_bot/bot.py /app/telegram_bot/
COPY telegram_bot/wait_for_model.sh /app/wait_for_model.sh
COPY telegram_bot/start_bot.sh /app/telegram_bot/

# Сделаем скрипты исполняемыми
RUN chmod +x /app/wait_for_model.sh /app/telegram_bot/start_bot.sh

# Запускаем скрипт, который дождется загрузки модели и затем запустит бота
ENTRYPOINT ["/bin/bash"]
CMD ["/app/telegram_bot/start_bot.sh"] 