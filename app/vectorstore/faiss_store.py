from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.config.settings import get_settings

import logging

logger = logging.getLogger(__name__)


class FAISSStore:
    """FAISS-based vector store with chunk_id mapping."""

    def __init__(self):
        self._index = None
        self._chunk_ids: list[str] = []
        self._dimension: int | None = None

    @property
    def index_path(self) -> Path:
        return get_settings().vectors_path / "faiss.index"

    @property
    def meta_path(self) -> Path:
        return get_settings().vectors_path / "faiss_meta.json"

    def _load(self) -> None:
        if self._index is not None:
            return

        import faiss

        if self.index_path.exists():
            self._index = faiss.read_index(str(self.index_path))
            self._dimension = self._index.d
            # Load chunk IDs
            if self.meta_path.exists():
                meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
                self._chunk_ids = meta.get("chunk_ids", [])
            logger.info(
                "Loaded FAISS index: %d vectors, dim=%d",
                self._index.ntotal,
                self._dimension,
            )
        else:
            logger.info("No existing FAISS index found")

    def _save(self) -> None:
        import faiss

        # Ensure directory exists
        index_dir = self.index_path.parent
        index_dir.mkdir(parents=True, exist_ok=True)
        if not index_dir.exists():
            logger.error("Failed to create directory: %s", index_dir)
            return

        faiss.write_index(self._index, str(self.index_path))  # type: ignore
        meta = {"chunk_ids": self._chunk_ids, "dimension": self._dimension}
        self.meta_path.write_text(json.dumps(meta), encoding="utf-8")

    def build(self, embeddings: list[list[float]], chunk_ids: list[str]) -> None:
        """Build FAISS index from embeddings."""
        import faiss

        if not embeddings:
            logger.warning("No embeddings to index")
            return

        vectors = np.array(embeddings, dtype=np.float32)
        self._dimension = vectors.shape[1]
        self._index = faiss.IndexFlatIP(self._dimension)  # Inner product (cosine after normalization)

        # Normalize for cosine similarity
        faiss.normalize_L2(vectors)
        self._index.add(vectors)
        self._chunk_ids = chunk_ids

        self._save()
        logger.info("Built FAISS index: %d vectors, dim=%d", len(chunk_ids), self._dimension)

    def add(self, embeddings: list[list[float]], chunk_ids: list[str]) -> None:
        """Add new embeddings to existing index."""
        self._load()

        if self._index is None:
            self.build(embeddings, chunk_ids)
            return

        import faiss

        vectors = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(vectors)
        self._index.add(vectors)  # type: ignore
        self._chunk_ids.extend(chunk_ids)

        self._save()

    def search(
        self, query_embedding: list[float], top_k: int = 10
    ) -> list[tuple[str, float]]:
        """Search for similar vectors. Returns list of (chunk_id, score)."""
        self._load()

        if self._index is None or self._index.ntotal == 0:  # type: ignore
            return []

        import faiss

        query = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query)

        k = min(top_k, self._index.ntotal)  # type: ignore
        scores, indices = self._index.search(query, k)  # type: ignore

        results: list[tuple[str, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self._chunk_ids):
                results.append((self._chunk_ids[idx], float(score)))

        return results

    def remove(self, chunk_ids: list[str]) -> None:
        """Remove vectors by chunk_id. Requires rebuild."""
        self._load()
        if self._index is None:
            return

        ids_to_remove = set(chunk_ids)
        keep_mask = [i for i, cid in enumerate(self._chunk_ids) if cid not in ids_to_remove]

        if len(keep_mask) == len(self._chunk_ids):
            return  # Nothing to remove

        if not keep_mask:
            # Remove everything
            import faiss
            self._index = faiss.IndexFlatIP(self._dimension)
            self._chunk_ids = []
        else:
            # Rebuild with kept vectors only
            import faiss
            vectors = np.array(
                [self._get_vector(i) for i in keep_mask], dtype=np.float32
            )
            self._index = faiss.IndexFlatIP(self._dimension)
            faiss.normalize_L2(vectors)
            self._index.add(vectors)
            self._chunk_ids = [self._chunk_ids[i] for i in keep_mask]

        self._save()

    def _get_vector(self, idx: int) -> list[float]:
        """Retrieve a vector by internal index."""
        import faiss
        vec = faiss.rev_swig_ptr(self._index.get_xb(), self._dimension, idx)  # type: ignore
        return vec.tolist()

    def count(self) -> int:
        self._load()
        if self._index is None:
            return 0
        return self._index.ntotal  # type: ignore

    def clear(self) -> None:
        self._index = None
        self._chunk_ids = []
        self._dimension = None
        if self.index_path.exists():
            self.index_path.unlink()
        if self.meta_path.exists():
            self.meta_path.unlink()
