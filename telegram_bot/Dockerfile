FROM python:3.11-slim AS builder

# Установка только необходимых инструментов для сборки
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    make \
    gnupg2 \
    lsb-release \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Копируем только файлы, необходимые для установки зависимостей
COPY pyproject.toml ./
COPY README.md ./
COPY Makefile ./

# Создаем виртуальное окружение и устанавливаем зависимости
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir wheel && \
    pip install --no-cache-dir ".[dev]" && \
    pip install --no-cache-dir -e . && \
    pip install --no-cache-dir openai>=1.0.0 haystack-ai[all]>=2.12.2 chroma-haystack>=3.0.0 && \
    pip install --no-cache-dir psycopg2-binary

# Второй этап: создание финального образа
FROM python:3.11-slim

# Установка необходимых для работы пакетов
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
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
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Создаем директории заранее для улучшения слоистости
WORKDIR /app
RUN mkdir -p /app/logs /app/telegram_bot

# Копируем виртуальное окружение из предыдущего этапа
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

# Копируем исходный код и конфигурации
COPY .env ./
COPY src /app/src
COPY scripts /app/scripts

# Копируем код бота и скрипты
COPY telegram_bot/bot.py /app/telegram_bot/
COPY telegram_bot/wait_for_model.sh /app/wait_for_model.sh
COPY telegram_bot/start_bot.sh /app/telegram_bot/

# Сделаем скрипты исполняемыми
RUN chmod +x /app/wait_for_model.sh /app/telegram_bot/start_bot.sh

# Настраиваем переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app:/app/src"

# Запускаем скрипт, который дождется загрузки модели и затем запустит бота
ENTRYPOINT ["/bin/bash"]
CMD ["/app/telegram_bot/start_bot.sh"] 
