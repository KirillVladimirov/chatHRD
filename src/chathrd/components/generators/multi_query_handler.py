"""Обработчики для мультизапросных поисковых сессий."""

import logging
from typing import List, Dict
from haystack.dataclasses import ChatMessage
from haystack import component

# Настройка логирования
logger = logging.getLogger(__name__)


@component
class MultiQueryHandler:
    """
    Для списка subqueries выполняет поиск+генерацию, а затем агрегирует ответы с логированием.
    """
    def __init__(
        self,
        bm25,
        chroma,
        joiner,
        ranker,
        prompt_builder,
        generator
    ):
        self.bm25 = bm25
        self.chroma = chroma
        self.joiner = joiner
        self.ranker = ranker
        self.pb = prompt_builder
        self.gen = generator
        self.logger = logging.getLogger(self.__class__.__name__)

    @component.output_types(answer=str)
    def run(self, multi: List[str], original_query: str) -> Dict[str, str]:
        self.logger.debug("Starting MultiQueryHandler.run: original_query='%s', multi=%s", original_query, multi)
        parts = []
        # Ограничиваем количество подзапросов тремя
        limited_multi = multi[:3]
        if len(multi) > 3:
            self.logger.debug("Ограничиваем число подзапросов с %d до 3", len(multi))

        for sq in limited_multi:
            self.logger.debug("Processing subquery: '%s'", sq)
            try:
                # retrieval
                d1 = self.bm25.run(query=sq)["documents"]
                self.logger.debug("BM25 returned %d documents", len(d1))
                d2 = self.chroma.run(query=sq)["documents"]
                self.logger.debug("Chroma returned %d documents", len(d2))

                # join + rank (reciprocal rank fusion)
                jdocs = self.joiner.run(documents=[d1, d2])["documents"]
                self.logger.debug("After joiner: %d documents", len(jdocs))
                rdocs = self.ranker.run(documents=jdocs, query=sq)["documents"]
                self.logger.debug("After ranker: %d documents", len(rdocs))

                # prompt & generation
                messages = self.pb.run(query=sq, documents=rdocs)["prompt"]
                self.logger.debug("Generated prompt messages: %s", messages)
                out = self.gen.run(messages)
                self.logger.debug("Generator output: %s", out)
                text = out.get("replies", [])[0].text or ""
                parts.append(text)
            except Exception as e:
                self.logger.error("Error processing subquery '%s': %s", sq, e, exc_info=True)

        if not parts:
            self.logger.debug("No parts generated, returning default message.")
            return {"answer": "Извините, по вашему запросу ничего не найдено."}

        # финальная агрегация
        summary = (
            f"На основе ответов на части вопроса «{original_query}» "
            "собери единый связный ответ:\n"
        )
        for i, p in enumerate(parts, 1):
            summary += f"Часть {i}: {p}\n"
        self.logger.debug("Aggregation prompt: %s", summary)
        sum_msg = ChatMessage.from_user(summary)
        sum_out = self.gen.run([sum_msg])
        agg = sum_out.get("replies", [])[0].text or ""
        self.logger.debug("Final aggregated answer: %s", agg)
        return {"answer": agg}
 