from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from trading_research.config import settings

try:
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    from langchain_openai import OpenAIEmbeddings
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:  # pragma: no cover
    Chroma = None
    Document = None
    OpenAIEmbeddings = None
    RecursiveCharacterTextSplitter = None


@dataclass
class RetrievedDocument:
    content: str
    metadata: dict[str, Any]


class ResearchVectorStore:
    def __init__(self, persist_directory: Path | None = None):
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self._store = None
        self._fallback_docs: list[RetrievedDocument] = []
        if Chroma and OpenAIEmbeddings and settings.openai_api_key:
            self._store = Chroma(
                collection_name="research_reports",
                persist_directory=str(self.persist_directory),
                embedding_function=OpenAIEmbeddings(model=settings.openai_embedding_model),
            )

    def ingest_text(self, text: str, metadata: dict[str, Any]) -> None:
        if self._store and RecursiveCharacterTextSplitter and Document:
            splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
            docs = splitter.split_documents([Document(page_content=text, metadata=metadata)])
            self._store.add_documents(docs)
            return
        self._fallback_docs.append(RetrievedDocument(content=text, metadata=metadata))

    def similarity_search(self, query: str, ticker: str | None = None, k: int = 3) -> list[RetrievedDocument]:
        if self._store:
            filter_dict = {"ticker": ticker} if ticker else None
            docs = self._store.similarity_search(query, k=k, filter=filter_dict)
            return [RetrievedDocument(content=doc.page_content, metadata=doc.metadata) for doc in docs]

        filtered = [
            doc for doc in self._fallback_docs if ticker is None or doc.metadata.get("ticker") == ticker
        ]
        ranked = sorted(filtered, key=lambda doc: query.lower() in doc.content.lower(), reverse=True)
        return ranked[:k]

