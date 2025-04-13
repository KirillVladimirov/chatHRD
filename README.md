# ChatHRD

Система для работы с HR документами.

## Описание проекта

**ChatHRD** — это прототип (MVP) поисковой системы на базе LLM, разрабатываемый для интеграции в систему кадрового электронного документооборота **VK HR Tek**.

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
├── Makefile               # Файл с командами для управления проектом (установка, очистка, работа с БД)
├── README.md              # Этот файл
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
│   └── file_report.md     # Отчет по типам скачанных файлов (генерируется)
├── notebooks/             # Директория для Jupyter ноутбуков
├── pyproject.toml         # Файл конфигурации проекта и зависимостей (PEP 621)
├── scripts/
│   ├── download_files.py  # Скрипт для скачивания файлов с фильтрацией по расширению
│   ├── generate_report.py # Скрипт для генерации отчета по скачанным файлам
│   ├── parse_documents.py # Скрипт для парсинга скачанных документов
│   ├── drop_databases.py  # Скрипт для удаления проектных БД
│   └── restore_databases.py # Скрипт для восстановления БД из дампов
├── src/
│   └── chathrd/           # Основной исходный код проекта
│       ├── __init__.py
│       ├── parsers/       # Модули для парсинга различных форматов файлов
│       └── main.py        # Точка входа в приложение (пример)
└── tests/                 # Директория для тестов
    ├── __init__.py
    ├── constants.py
    ├── test_parsers.py
    └── utils.py
```

## Развертывание проекта

1.  **Клонировать репозиторий:**
    ```bash
    git clone <URL репозитория>
    cd chathrd
    ```

2.  **Создать и активировать виртуальное окружение:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate # для Linux/macOS
    # .venv\Scripts\activate # для Windows
    ```

3.  **Настроить подключение к БД:**
    *   Скопируйте файл `.env.example` (если он есть) в `.env` или создайте `.env` вручную.
    *   Заполните файл `.env` учетными данными для вашего сервера PostgreSQL (версии 17+):
        ```dotenv
        PG_USER=ваш_пользователь
        PG_PASSWORD=ваш_пароль
        PG_HOST=localhost
        PG_PORT=5432
        PG_DB_INITIAL=postgres
        # DOWNLOAD_WORKERS=10 # Опционально: количество потоков для скачивания
        ```

4.  **Установить системные зависимости:**
    *   Для работы парсеров (включая OCR для PDF) требуются `tesseract`:
        ```bash
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr tesseract-ocr-rus # Для русского и английского языков
        ```
    *   Для генерации визуальных схем БД (опционально):
        ```bash
        sudo apt-get install -y graphviz
        ```

5.  **Установить Python зависимости:**
    Все зависимости проекта управляются через `pyproject.toml`.
    ```bash
    make install
    # или напрямую: pip install -e .[dev,notebooks] # Установить основные, для разработки и ноутбуков
    ```

6.  **Подготовить данные:**
    *   Убедитесь, что сервер PostgreSQL (версии 17+) запущен.
    *   Поместите файлы дампов (`cms.dump`, `lists.dump`, `filestorage.dump`) в директорию `data/raw/`.

7.  **Восстановить базы данных:**
    ```bash
    make restore-db
    ```
    Эта команда создаст базы данных `cms`, `lists`, `filestorage` и загрузит в них данные из дампов.

8.  **Скачать файлы:**
    ```bash
    make download-files
    ```
    Эта команда запустит многопоточное скачивание файлов из хранилища в директорию `data/downloaded_files/`. **Скачиваются только файлы с разрешенными расширениями** (см. `scripts/download_files.py`): `.pdf`, `.csv`, `.json`, `.doc`, `.docx`, `.epub`, `.txt`, `.xls`, `.xlsx`, `.yml`.
    По умолчанию используется 10 потоков (можно изменить переменной `DOWNLOAD_WORKERS` в `.env`).
    
    ```bash
    du -sh data/downloaded_files
    ```
    Эта команда позволяет измерить размер скачанных данных.

После выполнения этих шагов проект будет готов к работе.

## Развертывание с Docker

Для запуска проекта с использованием Docker и Docker Compose:

1.  **Установите Docker и Docker Compose:**
    Следуйте [официальной инструкции](https://docs.docker.com/engine/install/) для вашей ОС.
    Убедитесь, что ваш пользователь добавлен в группу `docker` (может потребоваться перезапуск терминала или системы).

2.  **Настройте файл `.env`:**
    Скопируйте `.env.example` в `.env` (если не сделали этого ранее) в корне проекта.
    Убедитесь, что файл `.env` содержит как минимум:
    ```dotenv
    TELEGRAM_BOT_TOKEN="ВАШ_ТОКЕН_БОТА"

    # Параметры для PostgreSQL в Docker (можно оставить по умолчанию)
    POSTGRES_USER=user
    POSTGRES_PASSWORD=password
    POSTGRES_DB=chathrd_db
    POSTGRES_PORT=5433 # Порт на хосте для доступа к БД в контейнере (по умолчанию 5433)

    # URL для LLM API (используется ботом внутри Docker)
    LLM_API_URL="http://llm_service:11434"
    ```
    Замените `ВАШ_ТОКЕН_БОТА` на реальный токен.

3.  **Соберите образы и запустите контейнеры:**
    В корневой директории проекта выполните:
    ```bash
    make docker-up
    ```

4.  **Проверка статуса:**
    ```bash
    make docker-ps
    ```
    Убедитесь, что сервисы `db`, `llm_service` и `telegram_bot` имеют статус `running`.

5.  **Просмотр логов:**
    ```bash
    make docker-logs     # Показать логи всех сервисов (нажмите Ctrl+C для выхода)
    make docker-logs-bot # Показать логи только бота (нажмите Ctrl+C для выхода)
    make docker-logs-llm # Показать логи только LLM сервиса (нажмите Ctrl+C для выхода)
    ```

6.  **Остановка контейнеров:**
    ```bash
    make docker-down   # Остановить и удалить контейнеры (тома сохраняются)
    make docker-down-v # Остановить, удалить контейнеры и том БД
    make docker-stop   # Просто остановить контейнеры (без удаления)
    ```

7.  **Доступ к БД из хоста:**
    Если вы оставили проброс порта в `docker-compose.yml` (по умолчанию на порт хоста `5433`), вы можете подключиться к базе данных в контейнере с помощью:
    *   Хост: `localhost`
    *   Порт: `5433` (или значение `POSTGRES_PORT` из `.env`)
    *   Пользователь/Пароль/БД: из `.env` (или `user`/`password`/`chathrd_db` по умолчанию)

8.  **Взаимодействие с Ollama:**
    *   После запуска контейнеров Ollama будет доступна внутри Docker сети по адресу `http://llm_service:11434`.
    *   Бот (`telegram_bot`) будет использовать этот адрес для отправки запросов к LLM, если переменная `LLM_API_URL` в `.env` установлена соответствующим образом (по умолчанию она установлена правильно).
    *   Для скачивания моделей и взаимодействия с Ollama изнутри контейнера `llm_service`, можно использовать команду:
      ```bash
      sudo docker compose exec llm_service ollama pull <название_модели>
      sudo docker compose exec llm_service ollama run <название_модели> "Ваш промпт"
      ```
    *   Если вы хотите иметь доступ к Ollama API с вашего хост-компьютера (например, для тестов через Postman или curl), раскомментируйте секцию `ports` для `llm_service` в `docker-compose.yml`.

## Запуск и настройка Telegram-бота

### Запуск локально (без Docker)

1.  Убедитесь, что выполнены шаги из раздела "Развертывание проекта" (виртуальное окружение активировано, зависимости установлены через `make install`).
2.  Убедитесь, что в файле `.env` в корне проекта указан `TELEGRAM_BOT_TOKEN`.
3.  Запустите бота командой:
    ```bash
    make run-telegram-bot
    ```
    Или напрямую:
    ```bash
    python telegram_bot/bot.py
    ```

### Запуск в Docker

Бот автоматически запускается как сервис `telegram_bot` при выполнении команды `docker compose up`. Его не нужно запускать отдельно.

### Настройка

Основная настройка бота производится через переменные окружения в файле `.env` в корне проекта:

*   `TELEGRAM_BOT_TOKEN` (обязательно): Токен, полученный от BotFather.
*   `DATABASE_URL` (для Docker настраивается автоматически): Строка подключения к базе данных. При локальном запуске бот может попытаться использовать эту переменную, если она задана.
*   `LLM_API_URL`: URL для подключения к LLM-сервису. При запуске в Docker должен указывать на `http://llm_service:11434` (значение по умолчанию в `.env.example`).

## Документация

Текстовые схемы баз данных в формате Mermaid ERD можно сгенерировать, запустив соответствующие ячейки в ноутбуке `notebooks/visualize_db_relations.ipynb`. Результаты сохраняются в директории `docs/` (`db_schema_*.md`) и могут быть добавлены в систему контроля версий. Эти файлы можно просматривать на платформах, поддерживающих Mermaid (например, GitHub).

Визуальные схемы (PNG) генерируются в `logs/db_diagrams/` при запуске ноутбука `notebooks/visualize_db_relations.ipynb` (требуется Graphviz).

## Дополнительные команды Makefile

*   `make clean`: Удалить временные файлы и кэш (`__pycache__`, `.pytest_cache` и т.д.).
*   `make format`: Отформатировать код с помощью Ruff.
*   `make lint`: Проверить код линтерами (Ruff, Mypy).
*   `make test`: Запустить тесты с помощью Pytest и сгенерировать отчет о покрытии.
*   `make install`: Установить проект и все зависимости (`.[dev,notebooks]`).
*   `make restore-db`: Восстановить базы данных из дампов (`data/raw/`).
*   `make drop-db`: **(Внимание!)** Удалить базы данных `cms`, `lists`, `filestorage`. Запрашивает подтверждение.
*   `make download-files`: Запустить **многопоточное** скачивание файлов из хранилища (только разрешенные расширения).
*   `make parse-docs`: Запустить парсинг скачанных документов в формат Markdown.
*   `make generate-report`: Сгенерировать отчет по типам скачанных файлов в `logs/file_report.md`.
*   `make check-system-deps`: Проверить наличие необходимых системных зависимостей (tesseract, graphviz).
*   `make run-telegram-bot`: Запустить Telegram бота локально (без Docker).
*   `make docker-up`: Собрать образы и запустить контейнеры Docker в фоновом режиме.
*   `make docker-down`: Остановить и удалить контейнеры Docker (тома сохраняются).
*   `make docker-down-v`: Остановить и удалить контейнеры и тома Docker.
*   `make docker-ps`: Показать статус контейнеров Docker.
*   `make docker-logs`: Показать логи всех контейнеров Docker (-f для слежения).
*   `make docker-logs-bot`: Показать логи контейнера telegram_bot (-f для слежения).
*   `make docker-logs-llm`: Показать логи контейнера llm_service (-f для слежения).
*   `make docker-stop`: Остановить запущенные контейнеры Docker (без удаления).
*   `make help`: Показать справку по всем доступным командам Makefile.

## Парсинг документов

Парсинг преобразует скачанные документы в единый формат Markdown для дальнейшей обработки и индексации.

-   **Расположение результатов:** `data/parsed_files/`
-   **Скрипт парсинга:** `scripts/parse_documents.py`
-   **Модули парсеров:** `src/chathrd/parsers/`

### Команда для запуска парсинга:
```bash
make parse-docs
```

### Поддерживаемые форматы для парсинга:

| Формат | Расширение | Поддержка OCR | Библиотека (основная) | Примечания                                 |
| :----- | :--------- | :------------ | :-------------------- | :----------------------------------------- |
| PDF    | `.pdf`     | Да            | `PyMuPDF` + `Pytesseract` | Извлекает текст; использует OCR для изображений |
| DOCX   | `.docx`    | Нет           | `python-docx`         | Извлекает текст и таблицы                   |
| XLSX   | `.xlsx`    | Нет           | `pandas`              | Извлекает данные из всех листов            |
| CSV    | `.csv`     | Нет           | `pandas`              | Преобразует в Markdown таблицу            |
| Text   | `.txt`     | Нет           | (встроенные)          | Читает как обычный текст                     |

**Примечание:** Файлы форматов `.doc`, `.json`, `.epub`, `.xls`, `.yml` скачиваются, но **в данный момент не парсятся** (для них нет реализованных парсеров в `src/chathrd/parsers/`). Парсер для них вернет `None`, и соответствующий `.md` файл не будет создан.

### Системные зависимости для парсинга:

-   `tesseract-ocr` и `tesseract-ocr-rus` (для OCR в PDF)

Установка на Ubuntu/Debian:
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-rus
```

## Использование

После установки зависимостей, восстановления БД и скачивания файлов, можно запустить парсинг:
```bash
make parse-docs
```
Результаты будут сохранены в `data/parsed_files/`.
