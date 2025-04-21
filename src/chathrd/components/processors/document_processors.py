"""Компоненты для обработки документов."""

from typing import List, Dict, Union
from haystack import component, Document
from pathlib import Path
from haystack.dataclasses import ByteStream


@component
class OverlapToStr:
    """
    Преобразует метаданные _split_overlap из списка словарей в строку формата "s:e".
    
    _split_overlap: [{'range': (s, e), …}] → "s:e"
    """
    @component.output_types(documents=List[Document])
    def run(self, documents: List[Document]) -> Dict[str, List[Document]]:
        for d in documents:
            ov = d.meta.get("_split_overlap")
            # ov = [{'range': (start, end), ...}]
            if (isinstance(ov, list) and ov
                    and isinstance(ov[0], dict)
                    and "range" in ov[0]):
                s, e = ov[0]["range"]
                d.meta["_split_overlap"] = f"{s}:{e}"
        return {"documents": documents}


@component
class EncodingSplitter:
    """
    Разделяет файлы на две группы по кодировке: UTF-8 и CP1251.
    """
    @component.output_types(utf8=List[str], cp=List[str])
    def run(self, sources: List[Union[str, Path, ByteStream]]) -> Dict[str, List[str]]:
        utf8_files, cp_files = [], []
        for src in sources:
            # превращаем путь в Path
            path = Path(src) if isinstance(src, (str, Path)) else None
            if not path:
                continue
            try:
                path.read_text(encoding="utf-8")
                utf8_files.append(str(path))
            except UnicodeDecodeError:
                cp_files.append(str(path))
        return {"utf8": utf8_files, "cp": cp_files}


@component
class QueryCleaner:
    """
    Приводит строку к нижнему регистру, токенизирует и оставляет только слово-числовые токены.
    """
    @component.output_types(query=str)
    def run(self, query: str) -> Dict[str, str]:
        import re
        from nltk.tokenize import word_tokenize
        
        q = query.lower()
        tokens = word_tokenize(q)
        filt = [t for t in tokens if re.fullmatch(r"\w+", t)]
        return {"query": " ".join(filt)} 