from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Chunk:
    id: str
    document_id: str
    text: str
    start_offset: int
    end_offset: int
    page: int | None = None
    section: str | None = None
    embedding_id: int | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
