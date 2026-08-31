from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import Protocol

import logging

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    text: str
    confidence: float
    bbox: list[list[int]] | None = None


class OCRProvider(Protocol):
    """Protocol for OCR engines."""

    def extract_text(self, image_path: Path) -> list[OCRResult]:
        """Extract text regions from an image."""
        ...

    def extract_all_text(self, image_path: Path) -> str:
        """Extract all text as a single string."""
        ...
