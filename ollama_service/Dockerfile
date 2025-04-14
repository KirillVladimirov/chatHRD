# Используем официальный образ Ollama как базовый
FROM ollama/ollama:latest

# Установка необходимых утилит
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Создаем директорию для логов
RUN mkdir -p /app/logs

# Копируем скрипт инициализации
COPY init.sh /init.sh
RUN chmod +x /init.sh

# Создаем директорию для моделей
VOLUME /root/.ollama

# Запускаем сервер Ollama с перенаправлением логов в файл
ENTRYPOINT ["sh", "-c", "ollama serve > /app/logs/ollama.log 2>&1"] 