from __future__ import annotations

from pathlib import Path

from app.extractors.base import ExtractedDocument, ExtractedChunk

import logging

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract text from PDF files using PyMuPDF, preserving page numbers."""

    SUPPORTED = {".pdf"}

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED

    def extract(self, path: Path) -> ExtractedDocument:
        try:
            import pymupdf
        except ImportError:
            logger.warning("PyMuPDF not installed. Cannot extract PDF: %s", path)
            return ExtractedDocument(
                chunks=[],
                metadata={"format": "pdf", "error": "PyMuPDF not installed"},
            )

        doc = pymupdf.open(str(path))
        chunks: list[ExtractedChunk] = []
        full_text_parts: list[str] = []
        total_pages = len(doc)

        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            text = page.get_text("text")

            if text.strip():
                full_text_parts.append(text)
                chunks.append(ExtractedChunk(
                    text=text,
                    start_offset=0,
                    end_offset=len(text),
                    page=page_num + 1,
                    section=f"Page {page_num + 1}",
                ))

        doc.close()

        if not chunks:
            full_text = "\n".join(full_text_parts)
            if full_text.strip():
                chunks.append(ExtractedChunk(
                    text=full_text,
                    start_offset=0,
                    end_offset=len(full_text),
                ))

        return ExtractedDocument(
            chunks=chunks,
            metadata={
                "format": "pdf",
                "pages": total_pages,
            },
        )
