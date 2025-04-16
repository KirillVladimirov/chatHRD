#!/bin/bash
set -e  # Выходить при ошибке

# Загружаем имя модели из переменной окружения или используем значение по умолчанию
MODEL_NAME="${MODEL_NAME:-hf.co/ruslandev/llama-3-8b-gpt-4o-ru1.0-gguf:Q8_0}"
STATUS_DIR="/tmp/ollama_status"
STATUS_FILE="${STATUS_DIR}/model_loaded"
# Внутри Docker сети используем имя сервиса "ollama" вместо localhost
OLLAMA_API_URL="${LLM_API_URL:-http://ollama:11434}"

echo "========================================================"
echo "Инициализация модели $MODEL_NAME"
echo "Используем API: $OLLAMA_API_URL"
echo "Статус-файл: $STATUS_FILE"
echo "========================================================"

# Создаем директорию для статус-файлов
mkdir -p "${STATUS_DIR}"

# Ожидаем, пока сервис Ollama полностью запустится
echo "Ожидаем запуск сервиса Ollama..."
sleep 5

# Проверяем доступность API
MAX_RETRIES=30
RETRY_COUNTER=0
until curl -s "${OLLAMA_API_URL}/api/version" > /dev/null || [ $RETRY_COUNTER -eq $MAX_RETRIES ]; do
    echo "Ожидаем доступность API Ollama... (попытка $((RETRY_COUNTER+1))/$MAX_RETRIES)"
    sleep 5
    RETRY_COUNTER=$((RETRY_COUNTER+1))
done

if [ $RETRY_COUNTER -eq $MAX_RETRIES ]; then
    echo "Ошибка: Сервис Ollama недоступен после $MAX_RETRIES попыток"
    exit 1
fi

echo "API Ollama доступен! Версия: $(curl -s ${OLLAMA_API_URL}/api/version)"

# Вывод информации о состоянии Ollama
echo "Список моделей в Ollama:"
curl -s "${OLLAMA_API_URL}/api/tags" | grep -A 5 "name"

# Проверяем, существует ли модель в списке доступных моделей
echo "Проверяем наличие модели..."
if ! curl -s "${OLLAMA_API_URL}/api/tags" | grep -q "$MODEL_NAME"; then
    echo "Модель не найдена, скачиваем..."
    curl -X POST "${OLLAMA_API_URL}/api/pull" -d "{\"name\":\"${MODEL_NAME}\"}"
    
    # Проверяем результат скачивания
    if ! curl -s "${OLLAMA_API_URL}/api/tags" | grep -q "$MODEL_NAME"; then
        echo "Ошибка при скачивании модели $MODEL_NAME"
        exit 1
    fi
fi

echo "Модель $MODEL_NAME найдена в списке доступных моделей"

# Проверка, загружена ли модель уже - пытаемся получить информацию о модели
MODEL_INFO=$(curl -s "${OLLAMA_API_URL}/api/show" -d "{\"name\":\"${MODEL_NAME}\"}")
echo "Информация о модели:"
echo "$MODEL_INFO"

# Проверка была ли модель уже использована через таймер для быстрого запроса
echo "Проверяем, загружена ли модель уже в память..."
start=$(date +%s)
RESPONSE=$(curl -s -m 3 "${OLLAMA_API_URL}/api/generate" -d "{\"model\":\"${MODEL_NAME}\",\"prompt\":\"test\",\"max_tokens\":1,\"stream\":false}")
end=$(date +%s)
elapsed=$((end-start))
echo "Время запроса: ${elapsed} секунд"
echo "Ответ модели:"
echo "$RESPONSE"

# Если запрос вернулся за менее чем 2 секунды и не содержит ошибки, модель уже загружена
if [ $elapsed -lt 2 ] && ! echo "$RESPONSE" | grep -q "error"; then
    echo "Модель уже загружена в память GPU (время ответа: ${elapsed} сек)"
    # Создаем статус-файл для индикации успешной загрузки модели
    echo "$(date) - Модель $MODEL_NAME уже была загружена в память" > "${STATUS_FILE}"
    echo "========================================================"
    echo "Модель $MODEL_NAME готова к использованию"
    echo "Статус записан в ${STATUS_FILE}"
    echo "========================================================"
    # Успешное завершение (контейнер завершит работу)
    exit 0
else
    echo "Модель требует полной загрузки в память (время ответа: ${elapsed} сек)"
    # При необходимости загрузки удаляем статус-файл, если он существует
    rm -f "${STATUS_FILE}"
fi

# Запускаем полный запрос, чтобы загрузить модель в память
echo "Загружаем модель в память..."
curl -s "${OLLAMA_API_URL}/api/generate" -d "{\"model\":\"${MODEL_NAME}\",\"prompt\":\"привет\",\"stream\":false}" > /tmp/model_response.json

# Проверяем, что ответ получен и не содержит ошибок
if grep -q "error" /tmp/model_response.json; then
    echo "Ошибка при загрузке модели в память:"
    cat /tmp/model_response.json
    exit 1
fi

echo "Модель успешно ответила на тестовый запрос"

# Создаем статус-файл для индикации успешной загрузки модели
echo "$(date) - Модель $MODEL_NAME успешно загружена" > "${STATUS_FILE}"
echo "========================================================"
echo "Модель $MODEL_NAME готова к использованию и загружена в память"
echo "Статус записан в ${STATUS_FILE}"
echo "========================================================"

# Успешное завершение (контейнер завершит работу)
exit 0
