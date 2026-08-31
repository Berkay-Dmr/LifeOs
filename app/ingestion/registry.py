from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

from app.database.repositories import (
    list_documents,
    count_documents,
    count_chunks,
    get_index_meta,
    set_index_meta,
)
from app.utils.hashing import sha256_text

import logging

logger = logging.getLogger(__name__)


@dataclass
class RegistryStats:
    documents: int = 0
    chunks: int = 0
    last_index_time: str | None = None
    root_directory: str | None = None


def get_registry_stats(root: Path) -> RegistryStats:
    """Get current registry statistics."""
    return RegistryStats(
        documents=count_documents(),
        chunks=count_chunks(),
        last_index_time=get_index_meta("last_index_time"),
        root_directory=str(root),
    )


def record_index_complete(root: Path) -> None:
    """Record that indexing completed successfully."""
    now = datetime.utcnow().isoformat()
    set_index_meta("last_index_time", now)
    set_index_meta("last_root", str(root))
    logger.info("Index completed at %s", now)


def get_index_fingerprint(root: Path) -> str:
    """Generate a fingerprint of the current root directory structure.

    Used to detect if the root has changed significantly since last index.
    """
    parts: list[str] = []
    if root.exists():
        for item in sorted(root.iterdir()):
            if item.is_dir():
                parts.append(f"d:{item.name}")
            else:
                parts.append(f"f:{item.name}:{item.stat().st_size}")
    return sha256_text("|".join(parts))
