from pathlib import Path

# Пути к директориям
TEST_FILES_DIR = Path(__file__).parent / "test_files"
REAL_FILES_DIR = Path(__file__).parent.parent.parent / "data" / "downloaded_files"

# Список реальных файлов для тестирования
REAL_TEST_FILES = [
    "zid_50_cat.pdf",
    "VK_HR_Tek_-_Описание_API_Документация_по_API_07.03.2024.pdf",
    "Чек-лист_бадди_для_новых_сотрудников_VK_Tech.pdf"
] 