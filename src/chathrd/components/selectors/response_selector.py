"""Компонент для выбора наиболее релевантного ответа из различных источников."""

from typing import List, Optional
from haystack.dataclasses import ChatMessage
from haystack import component


@component
class ResponseSelector:
    """
    Выбирает финальный ответ из:
      - multi_answer (если задан)
      - иначе rag_replies[0]
      - иначе chat_replies[0]
    """
    @component.output_types(answer=str)
    def run(
        self,
        chat_replies: Optional[List[ChatMessage]] = None,
        rag_replies:  Optional[List[ChatMessage]] = None,
        multi_answer: Optional[str]            = None
    ) -> dict:
        if multi_answer:
            return {"answer": multi_answer}
        if rag_replies:
            return {"answer": rag_replies[0].text}
        if chat_replies:
            return {"answer": chat_replies[0].text}
        return {"answer": ""}
