from __future__ import annotations

from pathlib import Path
from typing import Generator

from app.extractors.base import ExtractedDocument, ExtractedChunk, DocumentExtractor
from app.ocr.ocr_engine import get_ocr_engine
from app.ocr.preprocessor import preprocess_image, get_image_metadata, IMAGE_EXTENSIONS

import logging

logger = logging.getLogger(__name__)


class ImageExtractor:
    """Extract text from images using OCR."""

    def __init__(self, lang: str = "en"):
        self._lang = lang

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in IMAGE_EXTENSIONS

    def extract(self, path: Path) -> ExtractedDocument | None:
        try:
            metadata = get_image_metadata(path)
            preprocessed = preprocess_image(path)

            try:
                ocr = get_ocr_engine(lang=self._lang)
                full_text = ocr.extract_all_text(preprocessed)
            finally:
                if preprocessed != path and preprocessed.exists():
                    preprocessed.unlink(missing_ok=True)

            if not full_text.strip():
                return ExtractedDocument(
                    chunks=[ExtractedChunk(
                        text=f"[Image: {path.name}] (no text detected)",
                        start_offset=0,
                        end_offset=0,
                        metadata={"image_width": metadata.get("width"), "image_height": metadata.get("height")},
                    )],
                    metadata={"ocr_used": True, "text_found": False},
                )

            return ExtractedDocument(
                chunks=[ExtractedChunk(
                    text=full_text,
                    start_offset=0,
                    end_offset=len(full_text),
                    metadata={"image_width": metadata.get("width"), "image_height": metadata.get("height")},
                )],
                metadata={"ocr_used": True, "text_found": True},
            )

        except Exception as e:
            logger.warning("OCR failed for %s: %s", path.name, e)
            return ExtractedDocument(
                chunks=[ExtractedChunk(
                    text=f"[Image: {path.name}] (OCR failed: {e})",
                    start_offset=0,
                    end_offset=0,
                )],
                metadata={"ocr_error": str(e)},
            )

    def extract_chunks(self, path: Path) -> Generator[ExtractedChunk, None, None]:
        doc = self.extract(path)
        if doc:
            yield from doc.chunks
