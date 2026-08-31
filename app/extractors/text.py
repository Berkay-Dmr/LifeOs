from __future__ import annotations

from pathlib import Path

from app.extractors.base import ExtractedDocument, ExtractedChunk


class TextExtractor:
    """Extract content from plain text files (.txt)."""

    SUPPORTED = {".txt"}

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED

    def extract(self, path: Path) -> ExtractedDocument:
        text = _read_with_encoding_fallback(path)
        return ExtractedDocument(
            chunks=[
                ExtractedChunk(
                    text=text,
                    start_offset=0,
                    end_offset=len(text),
                )
            ],
            metadata={"format": "text"},
        )


def _read_with_encoding_fallback(path: Path) -> str:
    """Try UTF-8, then UTF-16, then Latin-1."""
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    # Last resort: read as bytes and decode with errors replaced
    return path.read_bytes().decode("utf-8", errors="replace")
