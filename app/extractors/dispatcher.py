from __future__ import annotations

from pathlib import Path

from app.extractors.base import ExtractedDocument, DocumentExtractor
from app.extractors.text import TextExtractor
from app.extractors.markdown import MarkdownExtractor
from app.extractors.code import CodeExtractor
from app.extractors.json_yaml import JSONExtractor, YAMLExtractor

import logging

logger = logging.getLogger(__name__)


def _get_all_extractors() -> list[DocumentExtractor]:
    """Lazy-load all extractors to avoid import errors for optional deps."""
    extractors: list[DocumentExtractor] = []

    # Always available
    extractors.append(MarkdownExtractor())
    extractors.append(CodeExtractor())
    extractors.append(JSONExtractor())
    extractors.append(YAMLExtractor())
    extractors.append(TextExtractor())

    # Optional: PDF
    try:
        import pymupdf  # noqa: F401
        from app.extractors.pdf import PDFExtractor
        extractors.append(PDFExtractor())
    except ImportError:
        logger.debug("PyMuPDF not installed, PDF extraction unavailable")

    # Optional: DOCX
    try:
        import docx  # noqa: F401
        from app.extractors.docx import DocxExtractor
        extractors.append(DocxExtractor())
    except ImportError:
        logger.debug("python-docx not installed, DOCX extraction unavailable")

    # Optional: OCR/Images
    try:
        from app.extractors.image import ImageExtractor
        extractors.append(ImageExtractor())
    except Exception:
        logger.debug("Image extractor unavailable (install Pillow)")

    return extractors


def extract_file(path: Path) -> ExtractedDocument | None:
    """Extract content from a file using the appropriate extractor.

    Returns None if no extractor can handle the file.
    """
    for extractor in _get_all_extractors():
        if extractor.can_handle(path):
            try:
                result = extractor.extract(path)
                logger.info(
                    "Extracted %s: %d chunks, format=%s",
                    path.name,
                    len(result.chunks),
                    result.metadata.get("format", "unknown"),
                )
                return result
            except Exception as e:
                logger.error("Extraction failed for %s: %s", path, e)
                return None

    logger.debug("No extractor for: %s", path.name)
    return None


def get_extractor(path: Path) -> DocumentExtractor | None:
    """Get the appropriate extractor for a file without extracting."""
    for extractor in _get_all_extractors():
        if extractor.can_handle(path):
            return extractor
    return None
