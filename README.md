# ChatHRD

Система интеллектуального поиска по HR документам на базе Docker.

## Описание проекта

**ChatHRD** — это прототип (MVP) поисковой системы на базе LLM, разрабатываемый для интеграции в систему кадрового электронного документооборота **VK HR Tek**. Проект полностью работает в Docker-контейнерах.

## Задача проекта

Основная задача — создать интеллектуальный поисковой модуль, способный:

*   Искать информацию по различным источникам корпоративного портала (базы знаний, документы, списки и т.д.).
*   Понимать запросы пользователей на естественном языке (семантический поиск).
*   Предоставлять релевантные ответы с указанием источников.
*   Учитывать права доступа пользователя.

## Структура проекта

Проект имеет следующую структуру:

```
/
├── src/                       # Исходный код пакета
│   └── chathrd/               # Основной пакет
│       ├── components/        # Компоненты пайплайнов
│       │   ├── converters/    # Конвертеры документов
│       │   ├── processors/    # Обработчики документов
│       │   ├── retrievers/    # Компоненты для поиска
│       │   ├── classifiers/   # Классификаторы запросов
│       │   ├── selectors/     # Селекторы ответов
│       │   └── generators/    # Компоненты для генерации ответов
│       ├── pipelines/         # Готовые пайплайны
│       │   ├── indexing.py    # Пайплайн индексации
│       │   └── querying.py    # Пайплайн для запросов
│       ├── utils/             # Вспомогательные функции
│       ├── cli/               # Интерфейс командной строки
│       └── config/            # Настройки проекта
├── telegram_bot/              # Телеграм бот
│   ├── bot.py                 # Основной файл бота
│   ├── start_bot.sh           # Скрипт запуска бота
│   ├── wait_for_model.sh      # Скрипт ожидания загрузки модели
│   └── Dockerfile             # Файл для сборки контейнера бота
├── scripts/                   # Скрипты для работы с данными
├── notebooks/                 # Jupyter ноутбуки для экспериментов
└── data/                      # Данные проекта
    ├── raw/                   # Сырые данные (дампы баз данных)
    ├── downloaded_files/      # Скачанные файлы
    ├── chroma_index/          # Индекс Chroma
    └── bm25.pkl               # Индекс BM25
```

## Развертывание проекта

### Требования

Для запуска проекта необходимы:

1. Docker и Docker Compose
2. Минимум 8 ГБ оперативной памяти (рекомендуется 16+ ГБ)
3. Около 25 ГБ свободного места на диске для файлов и моделей

### Шаги развертывания

1.  **Клонировать репозиторий:**
    ```bash
    git clone <URL репозитория>
    cd chathrd
    ```

2.  **Настройте файл `.env`:**
    Скопируйте `.env.example` в `.env` в корне проекта.
    Убедитесь, что файл `.env` содержит как минимум:
    ```dotenv
    TELEGRAM_BOT_TOKEN="ВАШ_ТОКЕН_БОТА"

    # Параметры для PostgreSQL в Docker
    POSTGRES_USER=user
    POSTGRES_PASSWORD=password
    POSTGRES_DB=chathrd_db
    POSTGRES_PORT=5433 # Порт на хосте для доступа к БД в контейнере

    # URL для LLM API (используется ботом внутри Docker)
    LLM_API_URL="http://ollama:11434"
    
    # Настройки для Ollama
    MODEL_NAME="hf.co/ruslandev/llama-3-8b-gpt-4o-ru1.0-gguf:Q4_K_M"
    OLLAMA_GPU_LAYERS="26" # Количество слоев модели на GPU (если есть)
    ```
    Замените `ВАШ_ТОКЕН_БОТА` на реальный токен.

3.  **Подготовка данных:**
    Поместите файлы дампов баз данных (`cms.dump`, `lists.dump`, `filestorage.dump`) в директорию `data/raw/`.

4.  **Запуск проекта:**
    ```bash
    sudo docker compose up -d
    ```
    
    Альтернативно:
    ```bash
    make docker-up
    ```

5.  **Восстановление баз данных:**
    ```bash
    sudo docker compose exec telegram_bot make restore-db
    ```

6.  **Скачивание файлов:**
    ```bash
    sudo docker compose exec telegram_bot make download-files
    ```
    Эта команда запустит многопоточное скачивание файлов из хранилища в директорию `data/downloaded_files/`.

7.  **Проверка статуса:**
    ```bash
    sudo docker compose ps
    ```
    
    Альтернативно:
    ```bash
    make docker-ps
    ```
    
    Убедитесь, что сервисы `db`, `ollama`, `model_initializer` и `telegram_bot` имеют статус `running` или `completed` (для `model_initializer`).

8.  **Альтернативный запуск бота (локально):**
    ```bash
    # Установка зависимостей
    pip install -e .
    
    # Запуск бота
    python telegram_bot/bot.py
    ```
    
    Примечание: перед запуском убедитесь, что:
    - Ollama сервис запущен и доступен по адресу http://localhost:11434
    - В файле .env указаны корректные настройки для локального запуска:
      ```
      MODEL_NAME="hf.co/IlyaGusev/saiga_yandexgpt_8b_gguf:Q4_0"
      LLM_API_URL="http://localhost:11434"
      ```

## Работа с проектом

### Просмотр логов

```bash
# Логи всех сервисов
sudo docker compose logs

# Логи телеграм-бота
sudo docker compose logs telegram_bot

# Логи Ollama
sudo docker compose logs ollama

# Постоянное отслеживание логов бота
sudo docker compose logs -f telegram_bot
```

Альтернативно с использованием `make`:
```bash
# Логи всех сервисов
make docker-logs

# Логи телеграм-бота
make docker-logs-bot

# Логи Ollama
make docker-logs-ollama

# Постоянное отслеживание логов бота
make docker-logs-bot-follow
```

### Индексация документов

Для индексации документов и создания базы знаний:

```bash
# Создание индекса Chroma и BM25 для скачанных документов в Docker
sudo docker compose exec telegram_bot chathrd-index --help

# Локальная установка (после установки пакета)
chathrd-index --help
```

Примеры использования:
```bash
# Индексировать все файлы из стандартной директории
sudo docker compose exec telegram_bot chathrd-index

# Индексировать конкретные файлы
sudo docker compose exec telegram_bot chathrd-index /path/to/file1.pdf /path/to/file2.docx

# Указать другие директории
sudo docker compose exec telegram_bot chathrd-index --data-dir /custom/data --index-dir /custom/index
```

Основные опции:
- `путь_к_файлам` - пути к файлам для индексации (если не указано, используются все файлы из data-dir)
- `--data-dir` - директория с файлами (по умолчанию: ../data/downloaded_files)
- `--index-dir` - директория для сохранения индекса (по умолчанию: ../data/chroma_index)
- `--bm25-path` - путь для сохранения BM25 индекса (по умолчанию: ../data/bm25.pkl)
- `--log-level` - уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Поиск информации через командную строку

Для выполнения запросов к индексированным документам:

```bash
# Поиск информации в индексе через Docker
sudo docker compose exec telegram_bot chathrd-query --help

# Локальная установка (после установки пакета)
chathrd-query --help
```

Примеры использования:
```bash
# Простой запрос
sudo docker compose exec telegram_bot chathrd-query "Как оформить отпуск?"

# Запрос с указанием модели и API
sudo docker compose exec telegram_bot chathrd-query "Порядок оформления больничного" --model-name "другая_модель" --api-url "http://custom-api/v1"

# Указание нестандартных путей к индексам
sudo docker compose exec telegram_bot chathrd-query "Процесс увольнения" --index-dir /path/to/index --bm25-path /path/to/bm25.pkl

# Запуск локально (не в Docker)
chathrd-query "Где найти инструкцию по подаче заявления на льготы?" --api-url http://localhost:11434/v1
```

Основные опции:
- `query` - текст запроса для поиска информации
- `--model-name` - имя модели LLM для генерации ответов (по умолчанию из settings/переменных окружения)
- `--api-url` - URL для API LLM (по умолчанию из settings/переменных окружения)
- `--index-dir` - директория с индексом Chroma (по умолчанию: ../data/chroma_index)
- `--bm25-path` - путь к индексу BM25 (по умолчанию: ../data/bm25.pkl)
- `--log-level` - уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Остановка проекта

```bash
# Остановить контейнеры (тома сохраняются)
sudo docker compose down

# Остановить контейнеры и удалить тома
sudo docker compose down -v

# Приостановить работу контейнеров без их удаления
sudo docker compose stop
```

Альтернативно с использованием `make`:
```bash
# Остановить контейнеры (тома сохраняются)
make docker-down

# Остановить контейнеры и удалить тома
make docker-down-volumes

# Приостановить работу контейнеров без их удаления
make docker-stop
```

## Взаимодействие с Telegram ботом

Бот автоматически запускается при старте контейнера `telegram_bot`. Для общения с ботом найдите его в Telegram по имени, которое вы указали при создании бота через BotFather.

### Основные команды бота:
- `/start` - Начать общение с ботом
- `/help` - Показать справку
- `/search <запрос>` - Поиск по базе знаний (альтернатива прямому вводу текста)
- `/feedback <текст>` - Отправить отзыв о работе бота

### Управление ботом:
```bash
# Перезапуск бота
sudo docker compose restart telegram_bot

# Просмотр логов бота
sudo docker compose logs -f telegram_bot
```

### Принцип работы с ботом:
1. Отправьте боту сообщение с вашим вопросом
2. Бот проведет поиск по базе знаний
3. Бот вернет ответ, сгенерированный на основе найденных документов
4. Все источники информации будут указаны в ответе

## Взаимодействие с LLM

Управление моделями Ollama:

```bash
# Скачать дополнительную модель
sudo docker compose exec ollama ollama pull <название_модели>

# Скачать рекомендуемую модель
sudo docker compose exec ollama ollama pull hf.co/ruslandev/llama-3-8b-gpt-4o-ru1.0-gguf:Q4_K_M

# Тестирование модели напрямую
sudo docker compose exec ollama ollama run <название_модели> "Ваш промпт"

# Просмотр списка скачанных моделей
sudo docker compose exec ollama ollama list

# Просмотр информации о модели
sudo docker compose exec ollama ollama show <название_модели>
```

## Управление данными

### Доступ к базе данных

Подключение к PostgreSQL из контейнера:

```bash
sudo docker compose exec telegram_bot psql -U $POSTGRES_USER -d cms
sudo docker compose exec telegram_bot psql -U $POSTGRES_USER -d lists
sudo docker compose exec telegram_bot psql -U $POSTGRES_USER -d filestorage
```

Для просмотра таблиц в базах данных:

```bash
# Просмотр списка таблиц в базе данных cms
sudo docker compose exec telegram_bot psql -U $POSTGRES_USER -d cms -c '\dt'

# Просмотр структуры конкретной таблицы
sudo docker compose exec telegram_bot psql -U $POSTGRES_USER -d cms -c '\d+ table_name'

# Просмотр содержимого таблицы
sudo docker compose exec telegram_bot psql -U $POSTGRES_USER -d cms -c 'SELECT * FROM table_name LIMIT 10;'
```

### Управление базами данных

```bash
# Восстановление баз данных из дампов
sudo docker compose exec telegram_bot make restore-db

# Удаление баз данных (требуется подтверждение)
sudo docker compose exec telegram_bot make drop-db
```

### Работа с файлами

```bash
# Скачивание файлов из хранилища
sudo docker compose exec telegram_bot make download-files

# Генерация отчета по типам файлов
sudo docker compose exec telegram_bot make generate-report

# Проверка размера скачанных данных
sudo docker compose exec telegram_bot du -sh /app/data/downloaded_files
```

## Дополнительные команды

Все команды запускаются внутри контейнера `telegram_bot`:

```bash
# Форматирование кода
sudo docker compose exec telegram_bot make format

# Проверка линтерами
sudo docker compose exec telegram_bot make lint

# Очистка временных файлов
sudo docker compose exec telegram_bot make clean

# Справка по доступным командам
sudo docker compose exec telegram_bot make help
```

## Поддерживаемые форматы для индексации

Система поддерживает индексацию следующих форматов документов через конвертеры Haystack:

| Формат | Расширение | Конвертер Haystack                  | Примечания                                 |
| :----- | :--------- | :---------------------------------- | :----------------------------------------- |
| PDF    | `.pdf`     | `PyPDFToDocument`                   | Извлекает текст и структуру из PDF документов |
| DOCX   | `.docx`    | `DOCXToDocument`                    | Извлекает текст и таблицы из Word документов   |
| XLSX   | `.xlsx`    | `ExcelToDocument`                   | Извлекает данные из Excel таблиц          |
| CSV    | `.csv`     | `CSVToDocument`                     | Преобразует CSV данные в документы         |
| Text   | `.txt`     | `TextFileToDocument`                | Обрабатывает текстовые файлы               |
| DOC    | `.doc`     | `DOCToDocument`                     | Обрабатывает файлы старого формата Word    |
| JSON   | `.json`    | `JSONToDocument`                    | Преобразует JSON данные в документы        |

Документы в любом из указанных форматов автоматически обрабатываются пайплайном индексации и доступны для поиска.

## Переменные окружения

Для настройки приложения можно использовать следующие переменные окружения:

- `DATA_DIR` - директория с данными
- `DOWNLOADED_FILES_DIR` - директория с скачанными файлами
- `CHROMA_INDEX_PATH` - путь к индексу Chroma
- `BM25_INDEX_PATH` - путь к индексу BM25
- `MODEL_NAME` - имя модели LLM
- `LLM_API_URL` - URL для API LLM
- `EMBEDDER_MODEL` - модель для создания эмбеддингов
- `MAX_SPLIT_LENGTH` - максимальная длина фрагмента для индексации
- `SPLIT_OVERLAP` - перекрытие фрагментов при индексации
- `TOP_K_RETRIEVAL` - количество документов для поиска
- `TOP_K_RANKER` - количество документов после ранжирования
- `TEMPERATURE` - температура генерации
- `MAX_TOKENS` - максимальное количество токенов для генерации
- `TELEGRAM_BOT_TOKEN` - токен для Telegram бота

## Устранение неполадок

### Проблемы с ботом
- **Бот не отвечает или работает некорректно**:
  1. Проверьте, загружена ли модель: `sudo docker compose logs ollama`
  2. Просмотрите логи бота: `sudo docker compose logs telegram_bot`
  3. Перезапустите бота: `sudo docker compose restart telegram_bot`
  4. Убедитесь, что LLM API доступен: `curl http://localhost:11434/api/health`

### Ошибки индексации
- **Ошибки при индексации документов**:
  1. Проверьте наличие файлов: `sudo docker compose exec telegram_bot ls -la /app/data/downloaded_files`
  2. Убедитесь, что достаточно места на диске: `df -h`
  3. Запустите индексацию с подробным логированием: `sudo docker compose exec telegram_bot chathrd-index --log-level DEBUG`

### Проблемы с производительностью
- **Медленная работа модели**:
  1. Проверьте использование GPU: `nvidia-smi`
  2. Отрегулируйте количество слоев на GPU: измените `OLLAMA_GPU_LAYERS` в `.env`
  3. Мониторьте использование ресурсов: `sudo docker stats`

### Проблемы с Docker
- **Конфликт портов**:
  1. Проверьте, какие порты заняты: `sudo lsof -i -P -n | grep LISTEN`
  2. Измените конфликтующие порты в `docker-compose.yml`
- **Ошибки прав доступа**:
  1. Проверьте права на директории данных: `sudo chmod -R 777 data/`
  2. Запустите Docker с правами root: `sudo docker compose up -d`
- **Контейнеры не запускаются**:
  1. Проверьте статус: `sudo docker compose ps`
  2. Посмотрите логи: `sudo docker compose logs`
  3. Перезапустите с пересозданием: `sudo docker compose up -d --force-recreate`
