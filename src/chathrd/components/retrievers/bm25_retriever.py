"""Компоненты для поиска документов с использованием BM25."""

import pickle
from pathlib import Path
from typing import List, Dict, Optional
from nltk.tokenize import word_tokenize

from haystack import component, Document
from haystack_integrations.document_stores.chroma import ChromaDocumentStore


@component
class BM25Builder:
    """
    Строит BM25‑индекс из списка документов и сохраняет его в файл.
    
    Вход:
      - documents: List[Document]  — документы с .content и .id
      - path     : str             — путь для сохранения (pickle)
    Выход:
      - documents: List[Document]  — тот же список документов
    """
    @component.output_types(documents=List[Document])
    def run(self, documents: List[Document], path: str = "../data/bm25.pkl") -> Dict[str, List[Document]]:
        # создаём папку, если её нет
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # подготавливаем корпус: токенизируем каждое содержание
        corpus = [
            word_tokenize(doc.content.lower() if doc.content else "")
            for doc in documents
        ]
        doc_ids = [doc.id for doc in documents]

        # строим индекс BM25L (можно BM25Okapi или BM25Plus)
        from rank_bm25 import BM25L
        bm25 = BM25L(corpus)

        # сохраняем в pickle: кортеж (bm25, doc_ids)
        with open(output_path, "wb") as f:
            pickle.dump((bm25, doc_ids), f)

        # возвращаем документы дальше по пайплайну
        return {"documents": documents}


@component
class PickledBM25Retriever:
    """
    Sparse Retriever на основе заранее построенного BM25-индекса в pickle.
    """
    def __init__(
        self,
        document_store: ChromaDocumentStore,
        path_to_pickle: str,
        top_k: int = 5
    ):
        self.top_k = top_k
        self.path = path_to_pickle
        # загрузка всех документов для быстрого доступа
        all_docs = document_store.filter_documents(filters={})
        self.doc_map = {d.id: d for d in all_docs}

    @component.output_types(documents=List[Document])
    def run(self, query: str, top_k: Optional[int] = None) -> Dict[str, List[Document]]:
        k = top_k or self.top_k
        with open(self.path, "rb") as f:
            bm25, doc_ids = pickle.load(f)
        tokens = word_tokenize(query.lower())
        scores = bm25.get_scores(tokens)
        top_idxs = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        docs = [self.doc_map[doc_ids[i]] for i in top_idxs if doc_ids[i] in self.doc_map]
        return {"documents": docs} 