# Используем официальный образ Ollama как базовый
FROM ollama/ollama:latest

# Установка необходимых утилит с использованием нескольких репозиториев и таймаутов
RUN apt-get update && \
    apt-get install -y --no-install-recommends apt-transport-https ca-certificates && \
    echo 'Acquire::ForceIPv4 "true";' > /etc/apt/apt.conf.d/99force-ipv4 && \
    echo 'Acquire::http::Timeout "60";' > /etc/apt/apt.conf.d/99timeout && \
    echo 'APT::Install-Recommends "false";' > /etc/apt/apt.conf.d/99norecommends && \
    apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Создаем директорию для логов
RUN mkdir -p /app/logs

# Копируем скрипт инициализации
COPY init.sh /init.sh
RUN chmod +x /init.sh

# Создаем директорию для моделей
VOLUME /root/.ollama

# Запускаем сервер Ollama с перенаправлением логов в файл
ENTRYPOINT ["sh", "-c", "ollama serve > /app/logs/ollama.log 2>&1"] 