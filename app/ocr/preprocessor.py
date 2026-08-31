from __future__ import annotations

from pathlib import Path
import tempfile

import logging

logger = logging.getLogger(__name__)


def preprocess_image(image_path: Path) -> Path:
    """Preprocess image for better OCR results.

    Returns path to preprocessed image (may be the same file if no changes).
    """
    try:
        from PIL import Image, ImageFilter, ImageEnhance
    except ImportError:
        logger.warning("Pillow not installed, skipping preprocessing")
        return image_path

    try:
        img = Image.open(image_path)

        # Convert to RGB if needed
        if img.mode not in ("L", "RGB"):
            img = img.convert("RGB")

        # Convert to grayscale for OCR
        if img.mode == "RGB":
            img = img.convert("L")

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)

        # Sharpen
        img = img.filter(ImageFilter.SHARPEN)

        # Save to temp file
        suffix = image_path.suffix or ".png"
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        img.save(tmp.name)
        return Path(tmp.name)

    except Exception as e:
        logger.warning("Image preprocessing failed: %s", e)
        return image_path


def get_image_metadata(image_path: Path) -> dict:
    """Get basic image metadata."""
    try:
        from PIL import Image
        img = Image.open(image_path)
        return {
            "width": img.width,
            "height": img.height,
            "mode": img.mode,
            "format": img.format,
        }
    except Exception:
        return {}


IMAGE_EXTENSIONS: set[str] = {
    ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".tif", ".webp",
}
