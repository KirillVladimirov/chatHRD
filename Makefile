# === Variables ===
PYTHON := python
PIP := pip
PYTHONPATH := $(shell pwd)

# === Targets ===
.PHONY: all clean install update restore-db drop-db download-files generate-report help lab generate-schema-docs parse-docs test lint format check-system-deps install-system-deps
.DEFAULT_GOAL := help

# === Setup ===
install-system-deps: ## Установить системные зависимости
	@echo "Установка системных зависимостей..."
	@command -v graphviz >/dev/null 2>&1 || { echo "Установка graphviz..."; sudo apt-get install -y graphviz; }
	@command -v antiword >/dev/null 2>&1 || { echo "Установка antiword..."; sudo apt-get install -y antiword; }
	@command -v unrtf >/dev/null 2>&1 || { echo "Установка unrtf..."; sudo apt-get install -y unrtf; }
	@command -v pandoc >/dev/null 2>&1 || { echo "Установка pandoc..."; sudo apt-get install -y pandoc; }
	@echo "Все системные зависимости установлены."

install: install-system-deps ## Установить проект и все зависимости (основные, dev, notebooks)
	@echo "Установка проекта и всех зависимостей..."
	$(PIP) install -e .[dev,notebooks]

update: install-system-deps ## Обновить проект и все зависимости до последних версий
	@echo "Обновление проекта и всех зависимостей..."
	$(PIP) install --upgrade -e .[dev,notebooks]

# === Development ===
lab: ## Запустить Jupyter Lab (БЕЗ АУТЕНТИФИКАЦИИ!)
	@echo "Запуск Jupyter Lab на http://localhost:8888/ (или http://<your-ip>:8888/)"
	@echo "ПРЕДУПРЕЖДЕНИЕ: Запуск без токена/пароля небезопасен!"
	@echo "Используйте Ctrl+C для остановки."
	jupyter lab --ip=0.0.0.0 --port=8888 --IdentityProvider.token=''

# === Database ===
restore-db: ## Восстановить базы данных (cms, lists, filestorage) из дампов
	@echo "Запуск восстановления баз данных..."
	$(PYTHON) scripts/restore_databases.py

drop-db: ## (!!!) Удалить проектные базы данных (cms, lists, filestorage)
	@echo "ВНИМАНИЕ! Запуск скрипта для УДАЛЕНИЯ баз данных!"
	$(PYTHON) scripts/drop_databases.py

# === Files ===
download-files: ## Скачать файлы контента (многопоточно)
	@echo "Запуск МНОГОПОТОЧНОГО скачивания файлов из хранилища..."
	$(PYTHON) scripts/download_files.py

generate-report: ## Сгенерировать отчет по скачанным файлам (logs/file_report.md)
	@echo "Генерация отчета по скачанным файлам..."
	$(PYTHON) scripts/generate_file_report.py

# === Maintenance ===
clean: ## Очистить проект от временных файлов (*.pyc, __pycache__, .coverage, etc.)
	@echo "Очистка временных файлов..."
	find . -type f -name '*.py[co]' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d -name '.pytest_cache' -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -exec rm -rf {} +
	find . -type d -name 'htmlcov' -exec rm -rf {} +
	find . -type f -name '.coverage*' -delete
	rm -rf build/ dist/ *.egg-info/

# === Testing ===
test: ## Запустить тесты с покрытием
	PYTHONPATH=$(PYTHONPATH) pytest tests/ -v --cov=chathrd

lint: ## Проверить код линтерами
	PYTHONPATH=$(PYTHONPATH) ruff check src/chathrd tests

format: ## Отформатировать код
	PYTHONPATH=$(PYTHONPATH) ruff format src/chathrd tests

# === Document Processing ===
parse-docs: check-system-deps ## Парсить документы из списка
	@echo "Парсинг документов..."
	@mkdir -p data/parsed_files
	@PYTHONPATH=$(PYTHONPATH) python scripts/parse_documents.py
	@echo "Результаты сохранены в data/parsed_files/"

check-system-deps: ## Проверить наличие системных зависимостей
	@command -v dot >/dev/null 2>&1 || { echo "Требуется graphviz. Установите: sudo apt-get install graphviz"; exit 1; }
	@command -v antiword >/dev/null 2>&1 || { echo "Требуется antiword. Установите: sudo apt-get install antiword"; exit 1; }
	@command -v unrtf >/dev/null 2>&1 || { echo "Требуется unrtf. Установите: sudo apt-get install unrtf"; exit 1; }
	@command -v pandoc >/dev/null 2>&1 || { echo "Требуется pandoc. Установите: sudo apt-get install pandoc"; exit 1; }
	@command -v tesseract >/dev/null 2>&1 || { echo "Требуется tesseract. Установите: sudo apt-get install tesseract-ocr tesseract-ocr-rus"; exit 1; }

# === Help ===
help: ## Показать это справочное сообщение
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)