from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, Any


@dataclass
class ExtractedChunk:
    """A single piece of extracted text with metadata."""
    text: str
    start_offset: int = 0
    end_offset: int = 0
    page: int | None = None
    section: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedDocument:
    """Full extraction result from a file."""
    chunks: list[ExtractedChunk]
    metadata: dict[str, Any] = field(default_factory=dict)
    language: str | None = None


class DocumentExtractor(Protocol):
    """Protocol for file content extractors."""

    def can_handle(self, path: Path) -> bool: ...

    def extract(self, path: Path) -> ExtractedDocument: ...
