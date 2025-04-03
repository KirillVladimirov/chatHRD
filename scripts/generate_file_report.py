import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import math

# Директория с файлами для анализа
SOURCE_DIR = Path("data") / "downloaded_files"
# Директория для отчетов
LOG_DIR = Path("logs")
# Имя файла отчета
REPORT_FILE = LOG_DIR / "file_report.md"

def human_readable_size(size_bytes: int, decimal_places: int = 2) -> str:
    """Конвертирует размер в байтах в читаемый формат (KB, MB, GB...)."""
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, decimal_places)
    return f"{s} {size_name[i]}"

def main() -> None:
    """Анализирует файлы и генерирует Markdown отчет."""
    project_root = Path(__file__).parent.parent
    source_full_dir = project_root / SOURCE_DIR
    log_full_dir = project_root / LOG_DIR
    report_full_path = project_root / REPORT_FILE

    if not source_full_dir.is_dir():
        print(f"Ошибка: Директория с файлами не найдена: {source_full_dir}", file=sys.stderr)
        sys.exit(1)

    # Убедимся, что директория для логов существует
    log_full_dir.mkdir(parents=True, exist_ok=True)

    print(f"Анализ файлов в директории: {source_full_dir}", file=sys.stderr)

    # Словарь для хранения статистики: {'.ext': {'count': N, 'total_size': M}}
    stats = defaultdict(lambda: {'count': 0, 'total_size': 0})
    total_files_processed = 0
    total_size_processed = 0

    for file_path in source_full_dir.rglob('*'):
        if file_path.is_file():
            total_files_processed += 1
            size = file_path.stat().st_size
            total_size_processed += size
            # Получаем расширение в нижнем регистре, или '.no_extension' если его нет
            extension = file_path.suffix.lower() if file_path.suffix else '.no_extension'
            stats[extension]['count'] += 1
            stats[extension]['total_size'] += size

    print(f"Анализ завершен. Обработано файлов: {total_files_processed}", file=sys.stderr)

    # --- Формирование Markdown отчета --- 
    report_lines = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_lines.append(f"# Отчет по файлам ({timestamp})")
    report_lines.append(f"\n**Источник:** `{source_full_dir}`")
    report_lines.append("\n## Статистика по расширениям")
    report_lines.append("\n| Расширение     | Количество | Общий размер |")
    report_lines.append("|----------------|------------|--------------|")

    # Сортируем расширения для упорядоченного вывода
    sorted_extensions = sorted(stats.keys())

    for ext in sorted_extensions:
        count = stats[ext]['count']
        size_bytes = stats[ext]['total_size']
        readable_size = human_readable_size(size_bytes)
        # Форматируем строку таблицы
        report_lines.append(f"| {ext:<14} | {count:>10} | {readable_size:>12} |")

    report_lines.append("\n## Общая статистика")
    report_lines.append(f"* **Всего файлов:** {total_files_processed}")
    report_lines.append(f"* **Общий размер:** {human_readable_size(total_size_processed)}")

    # --- Запись отчета в файл --- 
    try:
        with open(report_full_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines) + "\n")
        print(f"Отчет успешно сохранен в: {report_full_path}", file=sys.stderr)
    except OSError as e:
        print(f"Ошибка записи отчета в файл {report_full_path}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 