from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SearchResult:
    document_id: str
    chunk_id: str
    title: str
    path: str
    snippet: str
    score: float
    modified_at: str | None = None
    page: int | None = None
    section: str | None = None


@dataclass
class SearchQuery:
    text: str
    top_k: int = 10
    file_type: str | None = None
    folder: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    project: str | None = None
    language: str | None = None
