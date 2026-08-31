from __future__ import annotations

import re
from pathlib import Path

from app.extractors.base import ExtractedDocument, ExtractedChunk
from app.extractors.text import _read_with_encoding_fallback

import logging

logger = logging.getLogger(__name__)

# Extension to language mapping
EXTENSION_LANG: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".r": "r",
    ".R": "r",
    ".sql": "sql",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".ps1": "powershell",
    ".bat": "batch",
    ".cmd": "batch",
}

# Code file extensions
CODE_EXTENSIONS = set(EXTENSION_LANG.keys())


class CodeExtractor:
    """Extract content from source code files with language detection."""

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in CODE_EXTENSIONS

    def extract(self, path: Path) -> ExtractedDocument:
        text = _read_with_encoding_fallback(path)
        language = EXTENSION_LANG.get(path.suffix.lower(), "unknown")

        # Try to split by functions/classes
        chunks = _smart_split(text, language)

        if not chunks:
            chunks = [ExtractedChunk(
                text=text,
                start_offset=0,
                end_offset=len(text),
            )]

        return ExtractedDocument(
            chunks=chunks,
            metadata={"format": "code", "language": language},
            language=language,
        )


def _smart_split(text: str, language: str) -> list[ExtractedChunk]:
    """Try to split code by functions/classes/structs."""
    lines = text.split("\n")
    chunks: list[ExtractedChunk] = []

    if language == "python":
        chunks = _split_python(text, lines)
    elif language in ("javascript", "typescript"):
        chunks = _split_js_ts(text, lines)
    elif language in ("c", "cpp", "csharp", "java", "go", "rust"):
        chunks = _split_brace_language(text, lines)
    else:
        # Generic: split by blank lines into reasonable chunks
        chunks = _split_generic(text, lines)

    return chunks


def _split_python(text: str, lines: list[str]) -> list[ExtractedChunk]:
    chunks: list[ExtractedChunk] = []
    current_block: list[str] = []
    current_name = ""
    offset = 0
    block_start = 0

    for line in lines:
        match = re.match(r"^(class|def|async\s+def)\s+(\w+)", line)
        if match:
            if current_block:
                block_text = "\n".join(current_block)
                chunks.append(ExtractedChunk(
                    text=block_text,
                    start_offset=block_start,
                    end_offset=block_start + len(block_text),
                    section=current_name,
                ))
            current_name = match.group(0).strip()
            current_block = [line]
            block_start = offset
        else:
            current_block.append(line)

        offset += len(line) + 1

    if current_block:
        block_text = "\n".join(current_block)
        chunks.append(ExtractedChunk(
            text=block_text,
            start_offset=block_start,
            end_offset=block_start + len(block_text),
            section=current_name,
        ))

    return chunks


def _split_js_ts(text: str, lines: list[str]) -> list[ExtractedChunk]:
    chunks: list[ExtractedChunk] = []
    current_block: list[str] = []
    current_name = ""
    offset = 0
    block_start = 0

    for line in lines:
        match = re.match(
            r"^(export\s+)?(default\s+)?(function|class|const\s+\w+|let\s+\w+|var\s+\w+|interface\s+\w+|type\s+\w+)",
            line,
        )
        if match:
            if current_block:
                block_text = "\n".join(current_block)
                chunks.append(ExtractedChunk(
                    text=block_text,
                    start_offset=block_start,
                    end_offset=block_start + len(block_text),
                    section=current_name,
                ))
            current_name = match.group(0).strip()
            current_block = [line]
            block_start = offset
        else:
            current_block.append(line)

        offset += len(line) + 1

    if current_block:
        block_text = "\n".join(current_block)
        chunks.append(ExtractedChunk(
            text=block_text,
            start_offset=block_start,
            end_offset=block_start + len(block_text),
            section=current_name,
        ))

    return chunks


def _split_brace_language(text: str, lines: list[str]) -> list[ExtractedChunk]:
    chunks: list[ExtractedChunk] = []
    current_block: list[str] = []
    current_name = ""
    offset = 0
    block_start = 0

    for line in lines:
        match = re.match(
            r"^(public|private|protected|internal|static|async|void|int|string|class|struct|enum|interface|func|fn|def|function)\s+(\w+)",
            line,
        )
        if match:
            if current_block:
                block_text = "\n".join(current_block)
                chunks.append(ExtractedChunk(
                    text=block_text,
                    start_offset=block_start,
                    end_offset=block_start + len(block_text),
                    section=current_name,
                ))
            current_name = match.group(0).strip()
            current_block = [line]
            block_start = offset
        else:
            current_block.append(line)

        offset += len(line) + 1

    if current_block:
        block_text = "\n".join(current_block)
        chunks.append(ExtractedChunk(
            text=block_text,
            start_offset=block_start,
            end_offset=block_start + len(block_text),
            section=current_name,
        ))

    return chunks


def _split_generic(text: str, lines: list[str]) -> list[ExtractedChunk]:
    """Split by blank lines into chunks of ~50 lines."""
    chunks: list[ExtractedChunk] = []
    current_block: list[str] = []
    offset = 0
    block_start = 0

    for line in lines:
        current_block.append(line)
        if len(current_block) >= 50 or (not line.strip() and len(current_block) > 20):
            block_text = "\n".join(current_block)
            chunks.append(ExtractedChunk(
                text=block_text,
                start_offset=block_start,
                end_offset=block_start + len(block_text),
            ))
            block_start = offset + len(line) + 1
            current_block = []

        offset += len(line) + 1

    if current_block:
        block_text = "\n".join(current_block)
        chunks.append(ExtractedChunk(
            text=block_text,
            start_offset=block_start,
            end_offset=block_start + len(block_text),
        ))

    return chunks
