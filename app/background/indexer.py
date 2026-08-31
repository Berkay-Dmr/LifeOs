from __future__ import annotations

import time
import threading
from pathlib import Path
from typing import Callable

from app.utils.hashing import sha256_file
from app.database.repositories import get_document_hash
from app.extractors.dispatcher import extract_file
from app.database.sqlite import get_connection
from app.utils.text import count_tokens_approx
from app.utils.hashing import sha256_text

import logging

logger = logging.getLogger(__name__)


class BackgroundIndexer:
    """Indexes files in the background when changes are detected."""

    def __init__(self, root: Path, on_complete: Callable[[str], None] | None = None):
        self._root = root
        self._on_complete = on_complete
        self._queue: list[tuple[Path, str]] = []
        self._lock = threading.Lock()
        self._running = False
        self._worker_thread = None

    def start(self):
        """Start the background indexer worker."""
        self._running = True
        self._worker_thread = threading.Thread(
            target=self._worker, daemon=True
        )
        self._worker_thread.start()
        logger.info("Background indexer started")

    def _worker(self):
        """Worker that processes queued files."""
        while self._running:
            time.sleep(1)

            batch: list[tuple[Path, str]] = []
            with self._lock:
                batch = list(self._queue)
                self._queue.clear()

            for path, event_type in batch:
                try:
                    if event_type == "deleted":
                        self._handle_delete(path)
                    elif event_type == "modified" and path.exists():
                        self._handle_modify(path)
                except Exception as e:
                    logger.error("Index error for %s: %s", path, e)

    def queue_file(self, path: Path, event_type: str = "modified"):
        """Add a file to the indexing queue."""
        with self._lock:
            # Avoid duplicates
            existing = [p for p, _ in self._queue if p == path]
            if not existing:
                self._queue.append((path, event_type))
                logger.debug("Queued: %s (%s)", path.name, event_type)

    def _handle_modify(self, path: Path):
        """Index a single file."""
        from app.privacy.secrets import is_secret_file, redact_secrets
        from app.privacy.exclusions import should_skip_file

        if should_skip_file(path.name):
            return
        if is_secret_file(path):
            return

        # Check if changed
        current_hash = sha256_file(path)
        existing_hash = get_document_hash(str(path.relative_to(self._root)))

        if existing_hash == current_hash:
            return

        # Extract content
        doc = extract_file(path)
        if not doc:
            return

        # Store in database
        rel_path = str(path.relative_to(self._root))
        doc_id = sha256_text(rel_path)[:16]

        with get_connection() as conn:
            # Delete old chunks
            conn.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))

            # Upsert document
            conn.execute(
                """INSERT OR REPLACE INTO documents
                   (id, path, hash, mime_type, size_bytes, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))""",
                (
                    doc_id,
                    rel_path,
                    current_hash,
                    "application/octet-stream",
                    path.stat().st_size,
                ),
            )

            # Insert new chunks
            for i, chunk in enumerate(doc.chunks):
                chunk_id = f"{doc_id}_{i:04d}"
                text = chunk.text
                if is_secret_file(path):
                    text = redact_secrets(text)

                conn.execute(
                    """INSERT OR REPLACE INTO chunks
                       (id, document_id, content, chunk_index, start_offset, end_offset, section_title)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        chunk_id,
                        doc_id,
                        text,
                        i,
                        chunk.start_offset,
                        chunk.end_offset,
                        chunk.section,
                    ),
                )

            conn.commit()

        logger.info("Indexed: %s", rel_path)

        if self._on_complete:
            self._on_complete(f"Indexed: {rel_path}")

    def _handle_delete(self, path: Path):
        """Remove a file from the database."""
        rel_path = str(path.relative_to(self._root))
        doc_id = sha256_text(rel_path)[:16]

        with get_connection() as conn:
            conn.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
            conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()

        logger.info("Deleted from index: %s", rel_path)

        if self._on_complete:
            self._on_complete(f"Removed: {rel_path}")

    def stop(self):
        """Stop the indexer."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        logger.info("Background indexer stopped")

    @property
    def queue_size(self) -> int:
        with self._lock:
            return len(self._queue)
