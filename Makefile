.PHONY: clean

clean:
	find . -type f -name '*.py[co]' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '.pytest_cache' -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -exec rm -rf {} +
	find . -type d -name 'htmlcov' -exec rm -rf {} +
	find . -type f -name '.coverage*' -delete
	rm -rf build/ dist/ *.egg-info/

.PHONY: restore-db

restore-db:
	@echo "Запуск восстановления баз данных..."
	python scripts/restore_databases.py

.PHONY: drop-db

drop-db:
	@echo "ВНИМАНИЕ! Запуск скрипта для УДАЛЕНИЯ баз данных!"
	python scripts/drop_databases.py

.PHONY: install update

install:
	@echo "Установка проекта и всех зависимостей (основные, dev, notebooks)..."
	pip install -e .[dev,notebooks]

update:
	@echo "Обновление проекта и всех зависимостей..."
	pip install --upgrade -e .[dev,notebooks]

.PHONY: download-files

download-files:
	@echo "Запуск скачивания файлов из хранилища..."
	python scripts/download_files.py

.PHONY: download-files-threaded

download-files-threaded:
	@echo "Запуск МНОГОПОТОЧНОГО скачивания файлов из хранилища..."
	python scripts/download_files_threaded.py 