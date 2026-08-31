from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ChunkResult:
    text: str
    start_offset: int = 0
    end_offset: int = 0
    section: str | None = None
    page: int | None = None
    metadata: dict | None = None


class TextChunker(Protocol):
    def chunk(self, text: str, **kwargs) -> list[ChunkResult]: ...
