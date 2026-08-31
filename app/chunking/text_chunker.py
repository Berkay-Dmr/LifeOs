from __future__ import annotations

import re
from app.chunking.base import ChunkResult


class TextChunker:
    """Split text into chunks of ~max_tokens with overlap."""

    def __init__(self, max_tokens: int = 800, overlap_tokens: int = 100):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        # Approximate: 1 token ~ 4 chars
        self._max_chars = max_tokens * 4
        self._overlap_chars = overlap_tokens * 4

    def chunk(self, text: str, **kwargs) -> list[ChunkResult]:
        if not text.strip():
            return []

        # If short enough, return as single chunk
        if len(text) <= self._max_chars:
            return [ChunkResult(
                text=text,
                start_offset=0,
                end_offset=len(text),
            )]

        chunks: list[ChunkResult] = []
        start = 0

        while start < len(text):
            end = min(start + self._max_chars, len(text))

            # Try to break at sentence or paragraph boundary
            if end < len(text):
                break_at = _find_break_point(text, start, end)
                if break_at > start:
                    end = break_at

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(ChunkResult(
                    text=chunk_text,
                    start_offset=start,
                    end_offset=end,
                ))

            # Move forward with overlap
            start = end - self._overlap_chars
            if start <= (end - self._max_chars):
                start = end  # Prevent infinite loop

        return chunks


def _find_break_point(text: str, start: int, end: int) -> int:
    """Find the best place to break text (paragraph > sentence > word)."""
    search_region = text[start:end]

    # Try paragraph break (double newline)
    last_para = search_region.rfind("\n\n")
    if last_para > len(search_region) // 2:
        return start + last_para + 2

    # Try sentence break
    last_sentence = max(
        search_region.rfind(". "),
        search_region.rfind("? "),
        search_region.rfind("! "),
        search_region.rfind("\n"),
    )
    if last_sentence > len(search_region) // 3:
        return start + last_sentence + 2

    # Try word break
    last_space = search_region.rfind(" ")
    if last_space > len(search_region) // 3:
        return start + last_space + 1

    return end
