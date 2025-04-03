import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import requests
import psycopg2
from dotenv import load_dotenv

# Базовый URL, откуда скачивать файлы
BASE_DOWNLOAD_URL = "https://hackaton.hb.ru-msk.vkcloud-storage.ru/media"
# Директория для сохранения файлов
DOWNLOAD_DIR = Path("data") / "downloaded_files"

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
        print(f"Успешное подключение к БД '{db_name}'.")
        return conn
    except psycopg2.OperationalError as e:
        print(f"Ошибка подключения к БД '{db_name}': {e}")
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
            print(f"Найдено {len(files_to_download)} файлов в БД для скачивания.")
    except (Exception, psycopg2.Error) as error:
        print(f"Ошибка при выполнении запроса к БД: {error}")
        conn.rollback() # Откатываем транзакцию в случае ошибки
    finally:
        return files_to_download

def download_file(file_name: str, file_link: str, download_dir: Path) -> bool:
    """Скачивает один файл."""
    # Убираем возможный начальный слеш из link и соединяем с базовым URL
    relative_path = file_link.lstrip('/')
    full_url = f"{BASE_DOWNLOAD_URL}/{relative_path}"
    local_path = download_dir / file_name

    print(f"Скачивание '{file_name}' из {full_url} ... ", end="")

    try:
        response = requests.get(full_url, stream=True, timeout=30)
        response.raise_for_status() # Проверка на HTTP ошибки (4xx, 5xx)

        # Создаем директории, если их нет (на случай вложенных путей в имени файла, хотя тут вроде нет)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Успешно сохранено в {local_path}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Ошибка сети/HTTP: {e}")
        return False
    except OSError as e:
        print(f"Ошибка записи файла {local_path}: {e}")
        return False
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")
        return False

def main() -> None:
    """Основная функция скрипта."""
    project_root = Path(__file__).parent.parent
    dotenv_path = project_root / '.env'
    if not dotenv_path.exists():
        print(f"Ошибка: Файл .env не найден по пути {dotenv_path}")
        sys.exit(1)

    load_dotenv(dotenv_path=dotenv_path)

    pg_user = os.getenv("PG_USER")
    pg_password = os.getenv("PG_PASSWORD")
    pg_host = os.getenv("PG_HOST", "localhost")
    pg_port = os.getenv("PG_PORT", "5432")
    # Имя базы данных, где хранятся файлы
    filestorage_db_name = "filestorage"

    if not all([pg_user, pg_password]):
        print("Ошибка: Переменные PG_USER и PG_PASSWORD должны быть установлены в .env.")
        sys.exit(1)

    # Убедимся, что директория для скачивания существует
    download_full_dir = project_root / DOWNLOAD_DIR
    download_full_dir.mkdir(parents=True, exist_ok=True)
    print(f"Файлы будут сохранены в: {download_full_dir}")

    conn = None
    try:
        conn = get_db_connection(pg_user, pg_password, pg_host, pg_port, filestorage_db_name)
        if not conn:
            sys.exit(1)

        files_to_download = get_file_list_from_db(conn)

        if not files_to_download:
            print("Нет файлов для скачивания.")
            sys.exit(0)

        download_count = 0
        error_count = 0
        for file_name, file_link in files_to_download:
            if download_file(file_name, file_link, download_full_dir):
                download_count += 1
            else:
                error_count += 1

        print("\n--- Статистика скачивания ---")
        print(f"Успешно скачано: {download_count}")
        print(f"Ошибок: {error_count}")
        print("-----------------------------")

    finally:
        if conn:
            conn.close()
            print("Соединение с БД закрыто.")

if __name__ == "__main__":
    main() 