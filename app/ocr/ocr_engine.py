from __future__ import annotations

import warnings
from pathlib import Path

# Suppress torch quantization deprecation warnings
warnings.filterwarnings("ignore", message=".*quantize_per_tensor.*")
warnings.filterwarnings("ignore", message=".*pin_memory.*")

from app.ocr.base import OCRResult

import logging

logger = logging.getLogger(__name__)


class PaddleOCREngine:
    """PaddleOCR-based text extraction."""

    def __init__(self, lang: str = "en", use_gpu: bool = False):
        self._lang = lang
        self._use_gpu = use_gpu
        self._ocr = None

    def _load(self):
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
                self._ocr = PaddleOCR(
                    lang=self._lang,
                    use_angle_cls=True,
                    use_gpu=self._use_gpu,
                    show_log=False,
                )
                logger.info("PaddleOCR loaded (lang=%s)", self._lang)
            except ImportError:
                raise RuntimeError(
                    "PaddleOCR not installed. Run: pip install paddleocr paddlepaddle"
                )

    def extract_text(self, image_path: Path) -> list[OCRResult]:
        self._load()
        result = self._ocr.ocr(str(image_path), cls=True)

        if not result or not result[0]:
            return []

        results = []
        for line in result[0]:
            bbox = [[int(p[0]), int(p[1])] for p in line[0]]
            text = line[1][0]
            conf = float(line[1][1])
            results.append(OCRResult(text=text, confidence=conf, bbox=bbox))

        return results

    def extract_all_text(self, image_path: Path) -> str:
        results = self.extract_text(image_path)
        return "\n".join(r.text for r in results if r.text.strip())


class EasyOCREngine:
    """EasyOCR-based text extraction (fallback)."""

    def __init__(self, langs: list[str] | None = None, use_gpu: bool = False):
        self._langs = langs or ["en"]
        self._use_gpu = use_gpu
        self._reader = None

    def _load(self):
        if self._reader is None:
            try:
                import easyocr
                self._reader = easyocr.Reader(
                    self._langs, gpu=self._use_gpu
                )
                logger.info("EasyOCR loaded (langs=%s)", self._langs)
            except ImportError:
                raise RuntimeError(
                    "EasyOCR not installed. Run: pip install easyocr"
                )

    def extract_text(self, image_path: Path) -> list[OCRResult]:
        self._load()
        raw = self._reader.readtext(str(image_path))

        results = []
        for (bbox, text, conf) in raw:
            int_bbox = [[int(p[0]), int(p[1])] for p in bbox]
            results.append(OCRResult(text=text, confidence=conf, bbox=int_bbox))

        return results

    def extract_all_text(self, image_path: Path) -> str:
        results = self.extract_text(image_path)
        return "\n".join(r.text for r in results if r.text.strip())


def get_ocr_engine(lang: str = "en"):
    """Get the best available OCR engine."""
    # Try PaddleOCR first
    try:
        from paddleocr import PaddleOCR  # noqa: F401
        engine = PaddleOCREngine(lang=lang)
        engine._load()  # Test that it actually works
        return engine
    except Exception as e:
        logger.debug("PaddleOCR unavailable: %s", e)

    # Fallback to EasyOCR
    try:
        import easyocr  # noqa: F401
        engine = EasyOCREngine(langs=[lang])
        engine._load()  # Test that it actually works
        return engine
    except Exception as e:
        logger.debug("EasyOCR unavailable: %s", e)

    raise RuntimeError(
        "No OCR engine available. Install paddleocr or easyocr."
    )
