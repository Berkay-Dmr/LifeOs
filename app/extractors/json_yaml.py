from __future__ import annotations

import json
from pathlib import Path

from app.extractors.base import ExtractedDocument, ExtractedChunk
from app.extractors.text import _read_with_encoding_fallback

import logging

logger = logging.getLogger(__name__)


class JSONExtractor:
    """Extract content from JSON files."""

    SUPPORTED = {".json"}

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED

    def extract(self, path: Path) -> ExtractedDocument:
        text = _read_with_encoding_fallback(path)

        try:
            data = json.loads(text)
            pretty = json.dumps(data, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            pretty = text

        return ExtractedDocument(
            chunks=[
                ExtractedChunk(
                    text=pretty,
                    start_offset=0,
                    end_offset=len(pretty),
                )
            ],
            metadata={"format": "json"},
        )


class YAMLExtractor:
    """Extract content from YAML files."""

    SUPPORTED = {".yaml", ".yml"}

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED

    def extract(self, path: Path) -> ExtractedDocument:
        text = _read_with_encoding_fallback(path)

        # YAML is already readable as text, no need to parse
        return ExtractedDocument(
            chunks=[
                ExtractedChunk(
                    text=text,
                    start_offset=0,
                    end_offset=len(text),
                )
            ],
            metadata={"format": "yaml"},
        )
