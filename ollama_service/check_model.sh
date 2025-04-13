#!/bin/bash

# Загружаем имя модели из переменной окружения или используем значение по умолчанию
MODEL_NAME="${MODEL_NAME:-hf.co/ruslandev/llama-3-8b-gpt-4o-ru1.0-gguf:Q8_0}"
OLLAMA_URL=${OLLAMA_URL:-"http://localhost:11434"}

echo "Проверяем доступность сервиса Ollama..."
if ! curl -s "$OLLAMA_URL/api/tags" > /dev/null; then
    echo "Ошибка: Сервис Ollama недоступен по адресу $OLLAMA_URL"
    exit 1
fi

echo "Проверяем наличие модели $MODEL_NAME..."
if ! curl -s "$OLLAMA_URL/api/tags" | grep -q "$MODEL_NAME"; then
    echo "Ошибка: Модель $MODEL_NAME не найдена"
    exit 1
fi

echo "Тестируем запрос к модели..."
RESPONSE=$(curl -s "$OLLAMA_URL/api/generate" -d '{"model":"'"$MODEL_NAME"'","prompt":"Привет, как дела?","stream":false}')

if echo "$RESPONSE" | grep -q "error"; then
    echo "Ошибка при запросе к модели: $RESPONSE"
    exit 1
else
    echo "Успешно! Получен ответ от модели."
    echo "$RESPONSE" | grep -o '"response":"[^"]*"' | cut -d'"' -f4
fi

echo "Проверка завершена успешно!"
exit 0 