from __future__ import annotations

from app.chunking.base import ChunkResult


class CodeChunker:
    """Split code into chunks respecting function/class boundaries.

    This is a post-processor: if the extractor already split by
    functions/classes, this chunker merges small ones and splits
    large ones while preserving boundaries.
    """

    def __init__(self, max_tokens: int = 800, overlap_tokens: int = 50):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self._max_chars = max_tokens * 4

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

        # Split by blank lines into logical blocks
        blocks = _split_by_blocks(text)
        chunks: list[ChunkResult] = []
        current_text = ""
        current_start = 0

        for block_text, block_start in blocks:
            if len(current_text) + len(block_text) > self._max_chars and current_text:
                chunks.append(ChunkResult(
                    text=current_text.strip(),
                    start_offset=current_start,
                    end_offset=current_start + len(current_text),
                ))
                current_text = block_text
                current_start = block_start
            else:
                current_text += "\n\n" + block_text if current_text else block_text

        if current_text.strip():
            chunks.append(ChunkResult(
                text=current_text.strip(),
                start_offset=current_start,
                end_offset=current_start + len(current_text),
            ))

        return chunks


def _split_by_blocks(text: str) -> list[tuple[str, int]]:
    """Split code by blank lines into logical blocks."""
    blocks: list[tuple[str, int]] = []
    current_lines: list[str] = []
    offset = 0
    block_start = 0

    for line in text.split("\n"):
        if not line.strip() and current_lines:
            block_text = "\n".join(current_lines)
            blocks.append((block_text, block_start))
            current_lines = []
            block_start = offset + len(line) + 1
        else:
            current_lines.append(line)
        offset += len(line) + 1

    if current_lines:
        block_text = "\n".join(current_lines)
        blocks.append((block_text, block_start))

    return blocks
