from __future__ import annotations

import re
from pathlib import Path

from app.extractors.base import ExtractedDocument, ExtractedChunk
from app.extractors.text import _read_with_encoding_fallback


class MarkdownExtractor:
    """Extract content from Markdown files, preserving heading structure."""

    SUPPORTED = {".md", ".markdown", ".mdx"}

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED

    def extract(self, path: Path) -> ExtractedDocument:
        text = _read_with_encoding_fallback(path)
        sections = _parse_sections(text)

        chunks: list[ExtractedChunk] = []
        for section_text, heading_path, offset_start, offset_end in sections:
            chunks.append(ExtractedChunk(
                text=section_text,
                start_offset=offset_start,
                end_offset=offset_end,
                section=heading_path,
            ))

        if not chunks:
            chunks.append(ExtractedChunk(
                text=text,
                start_offset=0,
                end_offset=len(text),
            ))

        return ExtractedDocument(
            chunks=chunks,
            metadata={"format": "markdown"},
        )


def _parse_sections(text: str) -> list[tuple[str, str, int, int]]:
    """Split markdown into sections by headings.

    Returns list of (section_text, heading_path, start_offset, end_offset).
    """
    lines = text.split("\n")
    sections: list[tuple[str, str, int, int]] = []

    current_heading = ""
    heading_stack: list[tuple[int, str]] = []  # (level, title)
    section_lines: list[str] = []
    section_start = 0
    offset = 0

    for line in lines:
        match = re.match(r"^(#{1,6})\s+(.+)", line)
        if match:
            # Save previous section
            if section_lines or current_heading:
                section_text = "\n".join(section_lines)
                sections.append((
                    section_text,
                    current_heading,
                    section_start,
                    section_start + len(section_text),
                ))

            level = len(match.group(1))
            title = match.group(2).strip()

            # Update heading stack
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, title))
            current_heading = " > ".join(h for _, h in heading_stack)

            section_lines = [line]
            section_start = offset
        else:
            section_lines.append(line)

        offset += len(line) + 1  # +1 for newline

    # Don't forget the last section
    if section_lines:
        section_text = "\n".join(section_lines)
        sections.append((
            section_text,
            current_heading,
            section_start,
            section_start + len(section_text),
        ))

    return sections
