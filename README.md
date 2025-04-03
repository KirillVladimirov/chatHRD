# ChatHRD

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
│   └── raw/               # Директория для исходных данных (дампы БД)
├── docs/
│   ├── data_for_task.md   # Описание данных для задачи
│   └── specification.md   # Техническое задание
├── notebooks/             # Директория для Jupyter ноутбуков
├── pyproject.toml         # Файл конфигурации проекта и зависимостей (PEP 621)
├── scripts/
│   ├── drop_databases.py  # Скрипт для удаления проектных БД
│   └── restore_databases.py # Скрипт для восстановления БД из дампов
├── src/
│   └── chathrd/           # Основной исходный код проекта
│       ├── __init__.py
│       └── main.py        # Точка входа в приложение (пример)
└── tests/                 # Директория для тестов
    └── __init__.py
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
        ```

4.  **Установить зависимости:**
    ```bash
    make install
    ```
    Эта команда установит проект и все необходимые зависимости (основные, для разработки и для ноутбуков).

5.  **Подготовить данные:**
    *   Убедитесь, что сервер PostgreSQL (версии 17+) запущен.
    *   Поместите файлы дампов (`cms.dump`, `lists.dump`, `filestorage.dump`) в директорию `data/raw/`.

6.  **Восстановить базы данных:**
    ```bash
    make restore-db
    ```
    Эта команда создаст базы данных `cms`, `lists`, `filestorage` и загрузит в них данные из дампов.

7.  **Скачать файлы:**
    ```bash
    make download-files-threaded
    ```
    Эта команда запустит многопоточное скачивание файлов (контент из `filestorage`) с внешнего хранилища в директорию `data/downloaded_files/`. По умолчанию используется 10 потоков (можно изменить переменной `DOWNLOAD_WORKERS` в `.env`).
    
    ```bash
    du -sh data/downloaded_files
    ```
    Эта команда позволяет померить размер скаченных данных
    (Примечание: ожидаемый размер скачанных файлов около 8.8 ГБ).

После выполнения этих шагов проект будет готов к работе.

## Дополнительные команды Makefile

*   `make clean`: Удалить временные файлы и кэш.
*   `make update`: Обновить зависимости до последних версий.
*   `make restore-db`: Восстановить базы данных из дампов (`data/raw/`).
*   `make drop-db`: **(Внимание!)** Удалить базы данных `cms`, `lists`, `filestorage`. Запрашивает подтверждение.
*   `make download-files`: Запустить **многопоточное** скачивание файлов из хранилища.
*   `make generate-report`: Сгенерировать отчет по скачанным файлам в `logs/file_report.md`.
