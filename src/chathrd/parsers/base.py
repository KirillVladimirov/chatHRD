import os
import logging
from typing import List

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_file_title(file_path: str) -> str:
    """Получает заголовок файла из его имени."""
    return os.path.basename(file_path)

def process_text_blocks(blocks: List[str]) -> str:
    """Обрабатывает блоки текста, объединяя их в параграфы."""
    processed_blocks = []
    for block in blocks:
        if not block.strip():
            continue
        lines = block.split('\n')
        processed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            if line.startswith(('###', '##')):
                processed_lines.append('\n' + line + '\n')
                i += 1
                continue
            sentence = line
            while i + 1 < len(lines) and not lines[i + 1].strip().startswith(('###', '##')):
                next_line = lines[i + 1].strip()
                if not next_line:
                    break
                if sentence.endswith('-'):
                    sentence = sentence[:-1] + next_line
                elif any(sentence.endswith(p) for p in '.!?'):
                    processed_lines.append(sentence)
                    sentence = next_line
                else:
                    sentence += ' ' + next_line
                i += 1
            if sentence:
                processed_lines.append(sentence)
            i += 1
        processed_blocks.append('\n'.join(processed_lines))
    return '\n\n'.join(processed_blocks)

def remove_duplicates(lines: List[str]) -> List[str]:
    """Удаляет дубликаты строк, сохраняя порядок."""
    seen = set()
    return [line for line in lines if not (line in seen or seen.add(line))] 