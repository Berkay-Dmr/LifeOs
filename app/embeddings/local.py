from __future__ import annotations

import os
import hashlib
import json
from pathlib import Path

# Suppress HF Hub unauthenticated warnings
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

from app.config.settings import get_settings

import logging

logger = logging.getLogger(__name__)

# Models: name -> (dimension, description)
EMBEDDING_MODELS = {
    # Multilingual (supports Turkish)
    "paraphrase-multilingual-MiniLM-L12-v2": {
        "dim": 384,
        "desc": "Multilingual, good for Turkish (recommended)",
    },
    # English-optimized (better quality for English)
    "all-mpnet-base-v2": {
        "dim": 768,
        "desc": "Best quality English model",
    },
    # Fast & lightweight
    "all-MiniLM-L6-v2": {
        "dim": 384,
        "desc": "Fast, lightweight, English-focused",
    },
}

DEFAULT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


class LocalEmbedding:
    """Local embedding using sentence-transformers with disk cache."""

    def __init__(self, model_name: str | None = None):
        settings = get_settings()
        self._model_name = model_name or getattr(settings, "embedding_model", DEFAULT_MODEL) or DEFAULT_MODEL
        self._model = None
        self._dimension: int | None = None
        self._cache_dir = settings.data_path / "embedding_cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _load_model(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model: %s", self._model_name)
            self._model = SentenceTransformer(self._model_name)
            self._dimension = EMBEDDING_MODELS.get(self._model_name, {}).get("dim", 384)
            logger.info("Model loaded. Dimension: %d", self._dimension)
        except ImportError:
            raise RuntimeError(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )

    @property
    def dimension(self) -> int:
        self._load_model()
        return self._dimension  # type: ignore

    def embed(self, texts: list[str]) -> list[list[float]]:
        self._load_model()

        # Check cache for each text
        results: list[list[float] | None] = [None] * len(texts)
        to_embed: list[tuple[int, str]] = []

        for i, text in enumerate(texts):
            cached = self._get_cache(text)
            if cached is not None:
                results[i] = cached
            else:
                to_embed.append((i, text))

        # Embed uncached texts
        if to_embed:
            raw_texts = [t for _, t in to_embed]
            embeddings = self._model.encode(raw_texts, show_progress_bar=False)  # type: ignore

            for (idx, text), embedding in zip(to_embed, embeddings):
                vec = embedding.tolist()
                results[idx] = vec
                self._set_cache(text, vec)

        return [r for r in results if r is not None]  # type: ignore

    def embed_single(self, text: str) -> list[float]:
        return self.embed([text])[0]

    def _cache_key(self, text: str) -> str:
        h = hashlib.sha256(text.encode()).hexdigest()[:16]
        return f"{h}.json"

    def _get_cache(self, text: str) -> list[float] | None:
        cache_file = self._cache_dir / self._cache_key(text)
        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return None

    def _set_cache(self, text: str, embedding: list[float]) -> None:
        cache_file = self._cache_dir / self._cache_key(text)
        try:
            cache_file.write_text(
                json.dumps(embedding), encoding="utf-8"
            )
        except Exception as e:
            logger.warning("Failed to cache embedding: %s", e)
