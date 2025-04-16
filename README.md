# ChatHRD

Система для работы с HR документами на базе Docker.

## Описание проекта

**ChatHRD** — это прототип (MVP) поисковой системы на базе LLM, разрабатываемый для интеграции в систему кадрового электронного документооборота **VK HR Tek**. Проект полностью работает в Docker-контейнерах.

## Задача проекта

Основная задача — создать интеллектуальный поисковой модуль, способный:

*   Искать информацию по различным источникам корпоративного портала (базы знаний, документы, списки и т.д.).
*   Понимать запросы пользователей на естественном языке (семантический поиск).
*   Предоставлять релевантные ответы с указанием источников.
*   Учитывать права доступа пользователя.

## Структура проекта

```
.
├── .env                   # Файл с переменными окружения (учетные данные БД и т.д.)
├── .gitignore             # Файл для исключения файлов из Git
├── Makefile               # Файл с командами для управления проектом
├── README.md              # Этот файл
├── Modelfile              # Файл конфигурации для моделей Ollama
├── docker-compose.yml     # Конфигурация Docker для развертывания сервисов
├── data/
│   ├── downloaded_files/  # Скачанные файлы с разрешенными расширениями
│   ├── parsed_files/      # Документы, преобразованные в Markdown
│   └── raw/               # Директория для исходных данных (дампы БД)
├── docs/
│   ├── data_for_task.md   # Описание данных для задачи
│   ├── specification.md   # Техническое задание
│   ├── db_schema_cms.md   # Mermaid-схема БД cms (генерируется)
│   ├── db_schema_lists.md # Mermaid-схема БД lists (генерируется)
│   └── db_schema_filestorage.md # Mermaid-схема БД filestorage (генерируется)
├── logs/
│   ├── db_diagrams/       # Визуальные схемы БД (PNG, генерируются)
│   ├── download_errors.log # Лог ошибок скачивания файлов
│   ├── download_stats.log  # Лог статистики скачивания файлов
│   ├── bot.log            # Лог работы Telegram бота
│   ├── ollama.log         # Лог работы Ollama сервиса
│   └── file_report.md     # Отчет по типам скачанных файлов (генерируется)
├── llm_api_tests/         # Скрипты для тестирования LLM API
├── notebooks/             # Директория для Jupyter ноутбуков
├── ollama_service/        # Сервис Ollama для работы с LLM
├── pyproject.toml         # Файл конфигурации проекта и зависимостей (PEP 621)
├── project/               # Директория с документацией по проекту
├── scripts/               # Скрипты для работы с данными и БД
├── src/                   # Основной исходный код проекта
└── telegram_bot/          # Телеграм бот для взаимодействия с пользователем
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

### Парсинг документов

Для преобразования скачанных документов в формат Markdown:

```bash
sudo docker compose exec telegram_bot make parse-docs
```

Результаты будут сохранены в `data/parsed_files/`.

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
# Запуск тестов
sudo docker compose exec telegram_bot make test

# Форматирование кода
sudo docker compose exec telegram_bot make format

# Проверка линтерами
sudo docker compose exec telegram_bot make lint

# Очистка временных файлов
sudo docker compose exec telegram_bot make clean

# Справка по доступным командам
sudo docker compose exec telegram_bot make help
```

## Поддерживаемые форматы для парсинга

| Формат | Расширение | Поддержка OCR | Библиотека (основная) | Примечания                                 |
| :----- | :--------- | :------------ | :-------------------- | :----------------------------------------- |
| PDF    | `.pdf`     | Да            | `PyMuPDF` + `Pytesseract` | Извлекает текст; использует OCR для изображений |
| DOCX   | `.docx`    | Нет           | `python-docx`         | Извлекает текст и таблицы                   |
| XLSX   | `.xlsx`    | Нет           | `pandas`              | Извлекает данные из всех листов            |
| CSV    | `.csv`     | Нет           | `pandas`              | Преобразует в Markdown таблицу            |
| Text   | `.txt`     | Нет           | (встроенные)          | Читает как обычный текст                     |

**Примечание:** Файлы форматов `.doc`, `.json`, `.epub`, `.xls`, `.yml` скачиваются, но **в данный момент не парсятся** (для них нет реализованных парсеров в `src/chathrd/parsers/`). Парсер для них вернет `None`, и соответствующий `.md` файл не будет создан.
