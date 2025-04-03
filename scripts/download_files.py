import os
import sys
from pathlib import Path
import concurrent.futures
from typing import List, Tuple, Dict, Any
import requests
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

# Базовый URL, откуда скачивать файлы
BASE_DOWNLOAD_URL = "https://hackaton.hb.ru-msk.vkcloud-storage.ru/media"
# Директория для сохранения файлов
DOWNLOAD_DIR = Path("data") / "downloaded_files"
# Директория для логов
LOG_DIR = Path("logs")
# Файл для лога статистики
STATS_LOG_FILE = LOG_DIR / "download_stats.log"
# Файл для лога ошибок скачивания
ERROR_LOG_FILE = LOG_DIR / "download_errors.log"
# Количество потоков для скачивания
MAX_WORKERS = int(os.getenv("DOWNLOAD_WORKERS", "10"))

def get_db_connection(pg_user: str, pg_password: str, pg_host: str, pg_port: str, db_name: str):
    """Устанавливает соединение с БД PostgreSQL."""
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=pg_user,
            password=pg_password,
            host=pg_host,
            port=pg_port
        )
        print(f"Успешное подключение к БД '{db_name}'.", file=sys.stderr)
        return conn
    except psycopg2.OperationalError as e:
        print(f"Ошибка подключения к БД '{db_name}': {e}", file=sys.stderr)
        return None

def get_file_list_from_db(conn) -> List[Tuple[str, str]]:
    """Получает список файлов (имя, относительный путь) из БД filestorage."""
    files_to_download = []
    if not conn:
        return files_to_download

    query = """
        SELECT so.name, sv.link
        FROM storage_storageobject AS so
        JOIN storage_version AS sv ON so.version_id = sv.id
        WHERE so.type = 1 AND sv.link IS NOT NULL AND sv.link <> '';
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            files_to_download = [(row[0], row[1]) for row in results]
            print(f"Найдено {len(files_to_download)} файлов в БД для скачивания.", file=sys.stderr)
    except (Exception, psycopg2.Error) as error:
        print(f"Ошибка при выполнении запроса к БД: {error}", file=sys.stderr)
        conn.rollback()
    finally:
        return files_to_download

def download_file_worker(file_info: Tuple[str, str], download_dir: Path) -> Dict[str, Any]:
    """Скачивает один файл в рабочем потоке."""
    file_name, file_link = file_info
    relative_path = file_link.lstrip('/')
    full_url = f"{BASE_DOWNLOAD_URL}/{relative_path}"
    local_path = download_dir / file_name
    status: Dict[str, Any] = {"name": file_name, "success": False, "message": ""}

    try:
        # Проверяем, существует ли файл и его размер > 0, чтобы избежать повторного скачивания
        if local_path.exists() and local_path.stat().st_size > 0:
            status["success"] = True
            status["message"] = "Already exists"
            return status

        response = requests.get(full_url, stream=True, timeout=60) # Увеличен таймаут
        response.raise_for_status()

        local_path.parent.mkdir(parents=True, exist_ok=True)

        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        status["success"] = True
        status["message"] = f"Saved to {local_path}"
        return status

    except requests.exceptions.Timeout:
        status["message"] = f"Timeout downloading {full_url}"
        return status
    except requests.exceptions.RequestException as e:
        status["message"] = f"Network/HTTP error: {e}"
        return status
    except OSError as e:
        status["message"] = f"File write error {local_path}: {e}"
        return status
    except Exception as e:
        status["message"] = f"Unknown error: {e}"
        return status

def main() -> None:
    """Основная функция скрипта для многопоточного скачивания."""
    project_root = Path(__file__).parent.parent
    dotenv_path = project_root / '.env'
    if not dotenv_path.exists():
        print(f"Ошибка: Файл .env не найден по пути {dotenv_path}", file=sys.stderr)
        sys.exit(1)

    load_dotenv(dotenv_path=dotenv_path)

    pg_user = os.getenv("PG_USER")
    pg_password = os.getenv("PG_PASSWORD")
    pg_host = os.getenv("PG_HOST", "localhost")
    pg_port = os.getenv("PG_PORT", "5432")
    filestorage_db_name = "filestorage"

    if not all([pg_user, pg_password]):
        print("Ошибка: Переменные PG_USER и PG_PASSWORD должны быть установлены в .env.", file=sys.stderr)
        sys.exit(1)

    download_full_dir = project_root / DOWNLOAD_DIR
    download_full_dir.mkdir(parents=True, exist_ok=True)
    # Создаем директорию для логов
    log_full_dir = project_root / LOG_DIR
    log_full_dir.mkdir(parents=True, exist_ok=True)

    print(f"Файлы будут сохранены в: {download_full_dir}", file=sys.stderr)
    print(f"Используется потоков: {MAX_WORKERS}", file=sys.stderr)

    conn = None
    try:
        conn = get_db_connection(pg_user, pg_password, pg_host, pg_port, filestorage_db_name)
        if not conn:
            sys.exit(1)

        files_from_db = get_file_list_from_db(conn)
        total_files_in_db = len(files_from_db)

        if not files_from_db:
            print("Нет файлов в БД для скачивания.", file=sys.stderr)
            sys.exit(0)

        # Список для строк пре-анализа для лога
        pre_run_log_lines: List[str] = []

        # --- Анализ списка из БД --- 
        analysis_header = "--- Анализ списка из БД ---"
        print(analysis_header, file=sys.stderr)
        pre_run_log_lines.append(analysis_header)
        
        line = f"Всего записей файлов найдено в БД: {total_files_in_db}"
        print(line, file=sys.stderr); pre_run_log_lines.append(line)
        
        unique_db_names = {name.lower() for name, link in files_from_db}
        total_unique_files_in_db = len(unique_db_names)
        duplicate_db_entries = total_files_in_db - total_unique_files_in_db
        
        line = f"Количество дублирующихся записей по именам файлов: {duplicate_db_entries}"
        print(line, file=sys.stderr); pre_run_log_lines.append(line)
        line = f"Количество уникальных имен файлов в БД (ожидаемое число файлов): {total_unique_files_in_db}"
        print(line, file=sys.stderr); pre_run_log_lines.append(line)
        
        analysis_footer = "---------------------------"
        print(analysis_footer, file=sys.stderr)
        pre_run_log_lines.append(analysis_footer)

        # --- Предварительная проверка существующих файлов --- 
        print("\nСканирование существующих файлов...", file=sys.stderr)
        existing_files_set = set()
        for item in download_full_dir.rglob('*'):
            if item.is_file():
                existing_files_set.add(item.name.lower())
        line = f"Найдено {len(existing_files_set)} существующих файлов в {download_full_dir}"
        print(line, file=sys.stderr) # Эту строку не добавляем в pre_run лог, она информативная для консоли

        # --- Фильтрация списка для скачивания --- 
        files_to_attempt_download: List[Tuple[str, str]] = []
        for file_name, file_link in files_from_db:
            if file_name.lower() not in existing_files_set:
                files_to_attempt_download.append((file_name, file_link))
        
        files_to_process_count = len(files_to_attempt_download)
        skipped_due_to_existing = len({name.lower() for name, link in files_from_db} & existing_files_set)

        # --- Планирование скачивания --- 
        planning_header = "--- Планирование скачивания ---"
        print(f"\n{planning_header}", file=sys.stderr)
        pre_run_log_lines.append("") # Пустая строка для разделения
        pre_run_log_lines.append(planning_header)
        
        line = f"Уже существует локально (будет пропущено): {skipped_due_to_existing}"
        print(line, file=sys.stderr); pre_run_log_lines.append(line)
        line = f"Будет предпринята попытка скачать: {files_to_process_count} файлов"
        print(line, file=sys.stderr); pre_run_log_lines.append(line)
        
        planning_footer = "-----------------------------"
        print(planning_footer, file=sys.stderr)
        pre_run_log_lines.append(planning_footer)

        # --- Выход, если нечего скачивать --- 
        if files_to_process_count == 0:
            print("\nНет новых файлов для скачивания.", file=sys.stderr)
            # Формируем итоговую статистику для этого случая
            stats_header = "--- Статистика скачивания ---"
            stats_lines = [
                f"Всего файлов в списке БД: {total_files_in_db}",
                f"Успешно скачано новых: 0",
                f"Уже существовало (пропущено): {skipped_due_to_existing}",
                f"Ошибок скачивания: 0",
                "-----------------------------"
            ]
            # Записываем ВСЕ логи (пре-анализ и статистику) и выходим
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            project_root = Path(__file__).parent.parent
            try:
                log_file_path = project_root / STATS_LOG_FILE
                with open(log_file_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n=== {timestamp} ===\n")
                    # Записываем пре-анализ
                    for pre_line in pre_run_log_lines:
                        f.write(pre_line + "\n")
                    f.write("\n") # Отступ перед статистикой
                    # Записываем статистику
                    f.write(stats_header + "\n")
                    for stat_line in stats_lines:
                        f.write(stat_line + "\n")
                print(f"Статистика также записана в {log_file_path}", file=sys.stderr)
            except OSError as e:
                print(f"Ошибка записи статистики в лог-файл {log_file_path}: {e}", file=sys.stderr)
            sys.exit(0)

        # --- Запуск скачивания отфильтрованного списка --- 
        success_count = 0
        error_count = 0
        error_files_log: List[Tuple[str, str]] = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_file = {executor.submit(download_file_worker, file_info, download_full_dir): file_info
                              for file_info in files_to_attempt_download} # Используем отфильтрованный список

            print("\nЗапуск скачивания...", file=sys.stderr)
            processed_count = 0
            for future in concurrent.futures.as_completed(future_to_file):
                file_info = future_to_file[future]
                file_name = file_info[0]
                processed_count += 1 # Счетчик обработанных из тех, что пытались скачать
                try:
                    result = future.result()
                    # Лог префикс теперь относительно реально обрабатываемых
                    log_prefix = f"[{processed_count}/{files_to_process_count}]"
                    if result["success"]:
                        # Сообщение 'Already exists' из воркера теперь маловероятно, но обрабатываем на всякий случай
                        if result["message"] == "Already exists":
                            # Это не должно учитываться как новая ошибка или успех
                            print(f"{log_prefix} [Exists Check Worker] {file_name}") 
                        else:
                            success_count += 1
                            print(f"{log_prefix} [OK] {file_name}")
                    else:
                        error_count += 1
                        error_msg = result['message']
                        print(f"{log_prefix} [ERROR] {file_name}: {error_msg}")
                        error_files_log.append((file_name, error_msg))
                except Exception as exc:
                    error_count += 1
                    error_msg = str(exc)
                    log_prefix = f"[{processed_count}/{files_to_process_count}]"
                    print(f"{log_prefix} [FATAL ERROR] {file_name} сгенерировал исключение: {error_msg}")
                    error_files_log.append((file_name, f"FATAL EXCEPTION: {error_msg}"))

                # Прогресс-бар теперь тоже относительно реально обрабатываемых
                progress = int(50 * processed_count / files_to_process_count)
                bar = '█' * progress + '-' * (50 - progress)
                print(f"\rПрогресс: |{bar}| {processed_count}/{files_to_process_count} ({processed_count/files_to_process_count:.1%})", end="", file=sys.stderr)

        # --- Статистика (после скачивания) --- 
        stats_header = "--- Статистика скачивания ---"
        stats_lines = [
            f"Всего файлов в списке БД: {total_files_in_db}",
            f"Успешно скачано новых: {success_count}",
            f"Уже существовало (пропущено): {skipped_due_to_existing}",
            f"Ошибок скачивания (из {files_to_process_count} попыток): {error_count}",
            "-----------------------------"
        ]

        # Вывод статистики в stderr (как и было)
        print("\n\n" + stats_header, file=sys.stderr)
        for line in stats_lines:
            print(line, file=sys.stderr)

        # --- Запись логов --- 
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        project_root = Path(__file__).parent.parent 

        # Запись статистики в лог-файл (с добавлением пре-анализа)
        try:
            log_file_path = project_root / STATS_LOG_FILE
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(f"\n=== {timestamp} ===\n")
                # Записываем пре-анализ
                for pre_line in pre_run_log_lines:
                    f.write(pre_line + "\n")
                f.write("\n") # Отступ перед статистикой
                # Записываем статистику
                f.write(stats_header + "\n")
                for stat_line in stats_lines:
                    f.write(stat_line + "\n")
            print(f"Статистика также записана в {log_file_path}", file=sys.stderr)
        except OSError as e:
            print(f"Ошибка записи статистики в лог-файл {log_file_path}: {e}", file=sys.stderr)

        # Запись ошибок скачивания в лог-файл
        if error_files_log:
            try:
                error_log_path = project_root / ERROR_LOG_FILE
                with open(error_log_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n=== {timestamp} - Ошибки скачивания ===\n")
                    for fname, error_message in error_files_log:
                        f.write(f"{fname}: {error_message}\n")
                print(f"Список файлов с ошибками записан в {error_log_path}", file=sys.stderr)
            except OSError as e:
                print(f"Ошибка записи ошибок в лог-файл {error_log_path}: {e}", file=sys.stderr)
        else:
             print(f"Ошибок скачивания не было.", file=sys.stderr)

    finally:
        if conn:
            conn.close()
            print("Соединение с БД закрыто.", file=sys.stderr)

if __name__ == "__main__":
    main() 