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

        files_to_download = get_file_list_from_db(conn)

        if not files_to_download:
            print("Нет файлов для скачивания.", file=sys.stderr)
            sys.exit(0)

        total_files = len(files_to_download)
        success_count = 0
        error_count = 0
        already_exists_count = 0
        error_files_log: List[Tuple[str, str]] = [] # Список для имен файлов с ошибками

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Создаем задачи
            future_to_file = {executor.submit(download_file_worker, file_info, download_full_dir): file_info
                              for file_info in files_to_download}

            print("\nЗапуск скачивания...", file=sys.stderr)
            processed_count = 0
            for future in concurrent.futures.as_completed(future_to_file):
                file_info = future_to_file[future]
                file_name = file_info[0]
                processed_count += 1
                try:
                    result = future.result()
                    log_prefix = f"[{processed_count}/{total_files}]"
                    if result["success"]:
                        if result["message"] == "Already exists":
                            already_exists_count += 1
                            # print(f"{log_prefix} [Exists] {file_name}") # Раскомментировано для лога
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
                    log_prefix = f"[{processed_count}/{total_files}]"
                    print(f"{log_prefix} [FATAL ERROR] {file_name} сгенерировал исключение: {error_msg}")
                    error_files_log.append((file_name, f"FATAL EXCEPTION: {error_msg}"))

                # Прогресс-бар (простой текстовый)
                progress = int(50 * processed_count / total_files)
                bar = '█' * progress + '-' * (50 - progress)
                print(f"\rПрогресс: |{bar}| {processed_count}/{total_files} ({processed_count/total_files:.1%})", end="", file=sys.stderr)

        # --- Статистика --- 
        stats_header = "--- Статистика скачивания ---"
        stats_lines = [
            f"Всего файлов в списке: {total_files}",
            f"Успешно скачано новых: {success_count}",
            f"Уже существовало: {already_exists_count}",
            f"Ошибок скачивания: {error_count}",
            "----------------------------- AAAAAAAAAAAAAAAAAAA"
        ]

        # Вывод статистики в stderr (как и было)
        print("\n\n" + stats_header, file=sys.stderr)
        for line in stats_lines:
            print(line, file=sys.stderr)

        # --- Запись логов --- 
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        project_root = Path(__file__).parent.parent # Определяем здесь, чтобы было доступно

        # Запись статистики в лог-файл
        try:
            log_file_path = project_root / STATS_LOG_FILE
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(f"\n=== {timestamp} ===\n")
                f.write(stats_header + "\n")
                for line in stats_lines:
                    f.write(line + "\n")
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