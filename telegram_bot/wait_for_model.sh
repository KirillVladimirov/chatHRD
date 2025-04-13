#!/bin/bash
set -e  # Завершать при ошибках

# Файл индикатор, который создаётся в init.sh после загрузки модели
STATUS_DIR="/tmp/ollama_status"
STATUS_FILE="${STATUS_DIR}/model_loaded"
MAX_WAIT_TIME=300  # максимальное время ожидания в секундах (5 минут)
WAIT_INTERVAL=5    # интервал проверки в секундах
OLLAMA_API_URL="${LLM_API_URL:-http://ollama:11434}"  # URL для API
MODEL_NAME="${MODEL_NAME:-hf.co/ruslandev/llama-3-8b-gpt-4o-ru1.0-gguf:Q8_0}"  # Имя модели

echo "========================================================"
echo "Скрипт wait_for_model.sh запущен в $(date)"
echo "Ожидаем файл: $STATUS_FILE"
echo "Директория статусов: $STATUS_DIR"
echo "API URL: $OLLAMA_API_URL"
echo "Модель: $MODEL_NAME"
echo "========================================================"

# Функция для проверки доступности LLM API
check_llm_api() {
    echo "Проверяем API: $OLLAMA_API_URL, модель: $MODEL_NAME"
    
    # Проверяем доступность API
    if ! curl -s "${OLLAMA_API_URL}/api/version" > /dev/null; then
        echo "API недоступен: ${OLLAMA_API_URL}"
        return 1
    fi
    
    # Проверяем доступность модели
    if ! curl -s "${OLLAMA_API_URL}/api/tags" | grep -q "${MODEL_NAME}"; then
        echo "Модель недоступна: ${MODEL_NAME}"
        return 1
    fi
    
    # Проверяем работоспособность модели с помощью запроса
    local RESPONSE=$(curl -s "${OLLAMA_API_URL}/api/generate" -d "{\"model\":\"${MODEL_NAME}\",\"prompt\":\"тест\",\"stream\":false}")
    if echo "$RESPONSE" | grep -q "error"; then
        echo "Ошибка при запросе к модели: $RESPONSE"
        return 1
    fi
    
    echo "API и модель доступны и работают"
    return 0
}

echo "Ожидаем загрузки модели..."
elapsed_time=0

while [ $elapsed_time -lt $MAX_WAIT_TIME ]; do
    # Проверяем наличие директории и файла-индикатора
    if [ ! -d "$STATUS_DIR" ]; then
        echo "Директория $STATUS_DIR не существует, создаем..."
        mkdir -p "$STATUS_DIR"
    fi
    
    # Проверяем наличие файла-индикатора
    if [ -f "$STATUS_FILE" ]; then
        echo "Индикатор загрузки модели найден!"
        echo "Содержимое файла: $(cat $STATUS_FILE)"
        
        # Дополнительно проверяем API
        if check_llm_api; then
            echo "LLM API доступен и модель загружена. Запускаем бота!"
            echo "========================================================"
            exit 0
        else
            echo "Индикатор обнаружен, но API недоступен. Продолжаем ожидание..."
        fi
    else
        # Дополнительно проверяем API даже без наличия файла
        if check_llm_api; then
            echo "Индикатор не найден, но API доступен. Создаем индикатор..."
            echo "$(date) - Автоматически создан после обнаружения доступности API" > "$STATUS_FILE"
            echo "LLM API доступен и модель загружена. Запускаем бота!"
            echo "========================================================"
            exit 0
        fi
    fi
    
    echo "Ожидаем загрузки модели... (прошло $elapsed_time секунд из $MAX_WAIT_TIME)"
    sleep $WAIT_INTERVAL
    elapsed_time=$((elapsed_time + WAIT_INTERVAL))
done

echo "========================================================"
echo "Ошибка: превышено максимальное время ожидания ($MAX_WAIT_TIME секунд)"
echo "Проверьте состояние сервиса model_initializer и доступность модели"
echo "========================================================"
exit 1 