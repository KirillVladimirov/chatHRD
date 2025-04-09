import os
import pandas as pd
from pathlib import Path

# Создаем директорию для тестовых файлов
TEST_FILES_DIR = Path(__file__).parent / "test_files"
os.makedirs(TEST_FILES_DIR, exist_ok=True)

print(f"Создаю тестовые файлы в {TEST_FILES_DIR}")

# Создаем тестовый Excel файл
df = pd.DataFrame(
    {
        "Name": ["John", "Alice", "Bob"],
        "Age": [30, 25, 35],
        "City": ["New York", "London", "Paris"],
    }
)

excel_path = TEST_FILES_DIR / "example.xlsx"
df.to_excel(excel_path, index=False)
print(f"Создан файл {excel_path}")

# Создаем файл с неподдерживаемым расширением
xyz_path = TEST_FILES_DIR / "unsupported.xyz"
with open(xyz_path, "w") as f:
    f.write("This is an unsupported file type.")
print(f"Создан файл {xyz_path}")

# Проверяем созданные файлы
print("\nСозданные файлы:")
for file in TEST_FILES_DIR.iterdir():
    print(f"- {file.name} ({file.stat().st_size} bytes)")
