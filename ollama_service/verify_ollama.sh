#!/bin/bash
set -e

# Цвета для вывода в терминал
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Загружаем имя модели из переменной окружения или используем значение по умолчанию
MODEL_NAME="${MODEL_NAME:-hf.co/ruslandev/llama-3-8b-gpt-4o-ru1.0-gguf:Q8_0}"

echo -e "${YELLOW}Начинаем проверку работы Ollama...${NC}"

# Проверяем, работает ли Docker
echo -e "${YELLOW}Проверяем работу Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Ошибка: Docker не запущен или у вас нет прав для его использования${NC}"
    exit 1
fi
echo -e "${GREEN}Docker работает нормально${NC}"

# Проверяем, работает ли сервис Ollama
echo -e "${YELLOW}Проверяем доступность сервиса Ollama...${NC}"
if ! curl -s http://localhost:11434/api/version > /dev/null; then
    echo -e "${RED}Ошибка: Сервис Ollama недоступен. Запустите сервис через docker-compose up -d${NC}"
    exit 1
fi
echo -e "${GREEN}Сервис Ollama доступен${NC}"

# Проверяем, загружена ли модель
echo -e "${YELLOW}Проверяем наличие модели $MODEL_NAME...${NC}"
if ! curl -s http://localhost:11434/api/tags | grep -q "$MODEL_NAME"; then
    echo -e "${RED}Ошибка: Модель $MODEL_NAME не найдена${NC}"
    echo -e "${YELLOW}Пробуем загрузить модель...${NC}"
    curl -X POST http://localhost:11434/api/pull -d '{"name":"'"$MODEL_NAME"'"}'
    if ! curl -s http://localhost:11434/api/tags | grep -q "$MODEL_NAME"; then
        echo -e "${RED}Не удалось загрузить модель${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}Модель $MODEL_NAME найдена${NC}"

# Тестируем запрос к модели
echo -e "${YELLOW}Тестируем запрос к модели...${NC}"
echo -e "${YELLOW}Отправляем тестовый запрос: 'Привет, как дела?'${NC}"
RESPONSE=$(curl -s http://localhost:11434/api/generate -d '{"model":"'"$MODEL_NAME"'","prompt":"Привет, как дела?","stream":false}')

if echo "$RESPONSE" | grep -q "error"; then
    echo -e "${RED}Ошибка при запросе к модели: $RESPONSE${NC}"
    exit 1
else
    echo -e "${GREEN}Успешно! Получен ответ от модели:${NC}"
    echo -e "${GREEN}$(echo "$RESPONSE" | grep -o '"response":"[^"]*"' | cut -d'"' -f4)${NC}"
fi

echo -e "${GREEN}Все проверки завершены успешно! Сервис Ollama работает корректно и модель загружена.${NC}"
exit 0 