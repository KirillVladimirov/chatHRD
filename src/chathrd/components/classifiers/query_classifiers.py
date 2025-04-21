"""Компоненты для классификации и декомпозиции запросов."""

from typing import List, Dict
from haystack import component
from haystack.dataclasses import ChatMessage
from haystack.components.generators.chat import OpenAIChatGenerator


@component
class QueryClassifierLLM:
    """
    Классифицирует, нужен ли поиск (RAG) для запроса.
    """
    def __init__(self, generator: OpenAIChatGenerator):
        self.generator = generator
        self.template = """
Ты — классификатор запросов по базе знаний.
Если запрос требует поиска — ответь 'true'. Если можно ответить без поиска — 'false'.

Примеры:
Запрос: "Привет"
Ответ: false

Запрос: "Как дела?"
Ответ: false

Запрос: "Что такое GDPR?"
Ответ: true

Запрос: "Сколько дней отпуска положено сотрудникам?"
Ответ: true

Теперь классифицируй:
Запрос: "{{ query }}"
Ответ:
""".strip()

    @component.output_types(need_search=bool)
    def run(self, query: str) -> Dict[str, bool]:
        prompt = self.template.replace("{{ query }}", query)
        msg = ChatMessage.from_user(prompt)
        out = self.generator.run([msg])
        replies = out.get("replies", [])
        text = replies[0].text.strip().lower() if replies else ""
        return {"need_search": text.startswith("true")}


@component
class QueryDecomposerLLM:
    """
    Через LLM решает, нужно ли декомпозировать запрос, и генерирует subqueries.
    """
    def __init__(self, generator: OpenAIChatGenerator):
        self.generator = generator
        self.check_template = """
Ты — эксперт по обработке запросов.
Если запрос сложный и стоит разбить его на под‑вопросы — 'true', иначе — 'false'.

Примеры:
Запрос: "Расскажи о новых политиках отпуска и сколько дней теперь положено?"
Ответ: true

Запрос: "Что такое GDPR?"
Ответ: false

Теперь оцени:
Запрос: "{{ query }}"
Ответ:
""".strip()
        self.decomp_template = """
Ты — специалист по декомпозиции.
Разбей запрос на короткие независимые под‑вопросы, каждый на новой строке.

Примеры:
Оригинал: "Расскажи о новых политиках отпуска и сколько дней теперь положено?"
- Расскажи о новых политиках отпуска.
- Сколько дней отпуска теперь положено?

Теперь разбей:
Оригинал: "{{ query }}"
""".strip()

    @component.output_types(subqueries=List[str])
    def run(self, query: str) -> Dict[str, List[str]]:
        # 1) Проверяем необходимость разбивки
        check_prompt = self.check_template.replace("{{ query }}", query)
        check_msg = ChatMessage.from_user(check_prompt)
        check_out = self.generator.run([check_msg])
        dec = check_out.get("replies", [])
        needs = dec[0].text.strip().lower().startswith("true") if dec else False

        if not needs:
            return {"subqueries": [query]}

        # 2) Генерируем под‑вопросы
        decomp_prompt = self.decomp_template.replace("{{ query }}", query)
        decomp_msg = ChatMessage.from_user(decomp_prompt)
        decomp_out = self.generator.run([decomp_msg])
        raw = decomp_out.get("replies", [])[0].text or ""
        parts = [line.strip("- ").strip() for line in raw.splitlines() if line.strip()]
        return {"subqueries": parts} 
