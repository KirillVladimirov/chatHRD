# === Variables ===
PYTHON := python
PIP := pip

.PHONY: all clean install update restore-db drop-db download-files generate-report help
.DEFAULT_GOAL := help

# === Setup ===
install: ## Установить проект и все зависимости (основные, dev, notebooks)
	@echo "Установка проекта и всех зависимостей..."
	$(PIP) install -e .[dev,notebooks]

update: ## Обновить проект и все зависимости до последних версий
	@echo "Обновление проекта и всех зависимостей..."
	$(PIP) install --upgrade -e .[dev,notebooks]

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
	$(PYTHON) scripts/download_files_threaded.py

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

# === Help ===
help: ## Показать это справочное сообщение
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)