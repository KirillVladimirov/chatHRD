import os
import subprocess
import sys
from pathlib import Path
from typing import List

from dotenv import load_dotenv


def run_dropdb_command(pg_user: str, pg_password: str, pg_host: str, pg_port: str, db_name: str) -> bool:
    """Формирует и выполняет команду dropdb для указанной БД."""
    command: List[str] = [
        "dropdb",
        "--if-exists",
        "-h", pg_host,
        "-p", pg_port,
        "-U", pg_user,
        db_name
    ]

    print(f"\nПопытка удаления базы данных '{db_name}'...")
    # Не выводим пароль в лог
    masked_command_for_log = command[:]
    print(f"Выполнение: {' '.join(masked_command_for_log)}")

    try:
        # Передаем пароль через переменную окружения
        env = os.environ.copy()
        env['PGPASSWORD'] = pg_password
        process = subprocess.run(command, capture_output=True, text=True, check=True, env=env)
        print(f"Вывод dropdb для {db_name}:")
        # dropdb обычно ничего не выводит при успехе, но на всякий случай:
        if process.stdout:
            print("Stdout:")
            print(process.stdout)
        if process.stderr:
            print("Stderr:")
            print(process.stderr)
        print(f"База данных '{db_name}' успешно удалена (или не существовала).")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при удалении базы данных '{db_name}'!")
        print(f"Код возврата: {e.returncode}")
        print("Stdout:")
        print(e.stdout)
        print("Stderr:")
        print(e.stderr)
        return False
    except FileNotFoundError:
        print(f"Ошибка: Команда 'dropdb' не найдена. Убедитесь, что PostgreSQL установлен и dropdb доступен в PATH.")
        # Прерываем выполнение, так как команда недоступна
        sys.exit(1)

def main() -> None:
    """Основная функция скрипта."""
    project_root: Path = Path(__file__).parent.parent
    dotenv_path: Path = project_root / '.env'
    if not dotenv_path.exists():
        print(f"Ошибка: Файл .env не найден по пути {dotenv_path}")
        return

    load_dotenv(dotenv_path=dotenv_path)

    pg_user = os.getenv("PG_USER")
    pg_password = os.getenv("PG_PASSWORD")
    pg_host = os.getenv("PG_HOST", "localhost")
    pg_port = os.getenv("PG_PORT", "5432")

    if not all([pg_user, pg_password]):
        print("Ошибка: Переменные PG_USER и PG_PASSWORD должны быть установлены в .env файле.")
        return

    # Список баз данных для удаления
    databases_to_drop: List[str] = ["cms", "lists", "filestorage"]

    print("ВНИМАНИЕ! Этот скрипт удалит следующие базы данных:")
    for db_name in databases_to_drop:
        print(f" - {db_name}")
    print("Это действие необратимо!")

    confirmation = input("Вы уверены, что хотите продолжить? (введите 'yes'): ")

    if confirmation.lower() != 'yes':
        print("Отмена операции.")
        return

    print("\nНачало удаления баз данных...")
    all_successful = True
    for db_name in databases_to_drop:
        success = run_dropdb_command(pg_user, pg_password, pg_host, pg_port, db_name)
        if not success:
            all_successful = False
            # Продолжаем попытки удалить остальные БД

    if all_successful:
        print("\nВсе указанные базы данных успешно удалены (или не существовали).")
    else:
        print("\nУдаление баз данных завершено с ошибками.")

if __name__ == "__main__":
    main() 