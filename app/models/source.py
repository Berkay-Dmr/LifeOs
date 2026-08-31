from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Source:
    id: str
    memory_id: str
    document_id: str | None = None
    chunk_id: str | None = None
    source_type: str = "document"  # document | chunk | git | memory
