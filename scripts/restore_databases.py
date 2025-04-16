import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv


def run_restore_command(pg_user, pg_password, pg_host, pg_port, pg_db_initial, dump_file_path):
    """Формирует и выполняет команду pg_restore для указанного дампа."""
    connection_string = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db_initial}"
    command = [
        "pg_restore",
        "--create",
        "--dbname", connection_string,
        "--no-owner",
        "--format", "c",
        "--no-privileges",
        str(dump_file_path)
    ]

    print(f"\nЗапуск восстановления из {dump_file_path.name}...")
    print(f"Команда: {' '.join(command)}") # Выводим команду для отладки (без пароля)

    # Скрываем пароль при выводе
    masked_command_for_log = command[:].copy()
    masked_command_for_log[3] = f"postgresql://{pg_user}:******@{pg_host}:{pg_port}/{pg_db_initial}"
    print(f"Выполнение: {' '.join(masked_command_for_log)}")

    try:
        # Передаем пароль через переменную окружения, чтобы он не светился в ps
        env = os.environ.copy()
        env['PGPASSWORD'] = pg_password
        process = subprocess.run(command, capture_output=True, text=True, check=True, env=env)
        print(f"Вывод pg_restore для {dump_file_path.name}:")
        print(process.stdout)
        print(process.stderr)
        print(f"Восстановление {dump_file_path.name} успешно завершено.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при восстановлении {dump_file_path.name}!")
        print(f"Код возврата: {e.returncode}")
        print("Stdout:")
        print(e.stdout)
        print("Stderr:")
        print(e.stderr)
        return False
    except FileNotFoundError:
        print(f"Ошибка: Команда 'pg_restore' не найдена. Убедитесь, что PostgreSQL установлен и pg_restore доступен в PATH.")
        return False

def main():
    """Основная функция скрипта."""
    # Загружаем переменные из .env файла
    # Ищем .env в текущей директории или выше
    project_root = Path(__file__).parent.parent # Корень проекта (предполагаем, что скрипт в scripts/)
    dotenv_path = project_root / '.env'
    if not dotenv_path.exists():
        print(f"Ошибка: Файл .env не найден по пути {dotenv_path}")
        return

    load_dotenv(dotenv_path=dotenv_path)

    # Считываем параметры из переменных окружения
    pg_user = os.getenv("POSTGRES_USER")
    pg_password = os.getenv("POSTGRES_PASSWORD")
    pg_host = os.getenv("PG_HOST", "db")
    
    # Внутри Docker сети всегда используем стандартный порт 5432
    # Порт из переменной POSTGRES_PORT (5433) используется только для внешнего доступа
    pg_port = "5432"  # Внутренний порт PostgreSQL в контейнере всегда 5432
    
    pg_db_initial = os.getenv("PG_DB_INITIAL", "postgres")

    if not all([pg_user, pg_password]):
        print("Ошибка: Переменные POSTGRES_USER и POSTGRES_PASSWORD должны быть установлены в .env файле.")
        return

    # Определяем путь к директории с дампами
    dumps_dir = project_root / "data" / "raw"
    if not dumps_dir.is_dir():
        print(f"Ошибка: Директория с дампами не найдена: {dumps_dir}")
        return

    # Список дампов для восстановления
    dump_files = ["cms.dump", "lists.dump", "filestorage.dump"]

    all_successful = True
    for dump_filename in dump_files:
        dump_file_path = dumps_dir / dump_filename
        if not dump_file_path.is_file():
            print(f"Предупреждение: Файл дампа не найден: {dump_file_path}, пропуск.")
            all_successful = False
            continue

        success = run_restore_command(pg_user, pg_password, pg_host, pg_port, pg_db_initial, dump_file_path)
        if not success:
            all_successful = False
            print(f"Восстановление остановлено из-за ошибки с {dump_filename}.")
            break # Останавливаемся при первой ошибке

    if all_successful:
        print("\nВсе базы данных успешно восстановлены.")
    else:
        print("\nВосстановление завершено с ошибками.")

if __name__ == "__main__":
    main() 