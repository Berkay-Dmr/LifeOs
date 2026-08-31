from __future__ import annotations

import os
import uuid
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

from app.config.settings import LifeOSSettings
from app.utils.hashing import sha256_file
from app.utils.paths import relative_to_root
from app.privacy.exclusions import should_skip_dir, should_skip_file
from app.privacy.secrets import is_secret_file
from app.database.repositories import (
    get_document_hash,
    insert_document,
    insert_chunk,
    delete_chunks_for_document,
    list_documents,
    delete_document,
)
from app.models.document import Document
from app.models.chunk import Chunk
from app.extractors.dispatcher import extract_file

import logging

logger = logging.getLogger(__name__)


@dataclass
class ScanStats:
    total: int = 0
    new: int = 0
    changed: int = 0
    skipped: int = 0
    deleted: int = 0
    secret_filtered: int = 0
    extracted: int = 0
    extract_errors: int = 0
    error: int = 0


def scan_directory(root: Path, settings: LifeOSSettings) -> ScanStats:
    """Scan root directory and index new/changed files with extraction.

    Flow per file:
      exists in DB?
        → NO  → hash → insert → extract → store chunks
        → YES → hash changed?
                   → YES → re-index → re-extract
                   → NO  → skip
    """
    stats = ScanStats()

    if not root.exists():
        logger.error("Root directory does not exist: %s", root)
        return stats

    # Get existing hashes from DB
    existing_db_paths: set[str] = set()
    for doc in list_documents():
        existing_db_paths.add(doc.path)

    found_paths: set[str] = set()

    for dirpath, dirnames, filenames in os.walk(root):
        dir_path = Path(dirpath)

        # Filter skipped directories in-place
        dirnames[:] = [
            d for d in dirnames
            if not should_skip_dir(d)
        ]

        for fname in filenames:
            file_path = dir_path / fname
            stats.total += 1

            if should_skip_file(file_path):
                stats.skipped += 1
                continue

            rel_path = relative_to_root(file_path, root)
            if rel_path is None:
                stats.skipped += 1
                continue

            found_paths.add(rel_path)

            # Skip secret files
            if is_secret_file(file_path):
                stats.secret_filtered += 1
                logger.info("Secret file skipped: %s", rel_path)
                continue

            try:
                stat = file_path.stat()
                size = stat.st_size

                # Skip oversized files
                if size > settings.max_file_size_mb * 1024 * 1024:
                    stats.skipped += 1
                    continue

                content_hash = sha256_file(file_path)
                old_hash = get_document_hash(rel_path)

                if old_hash is None:
                    # New file
                    _index_and_extract(file_path, rel_path, content_hash, stat)
                    stats.new += 1
                    stats.extracted += 1
                    logger.info("New: %s", rel_path)
                elif old_hash != content_hash:
                    # Changed file — re-index and re-extract
                    _reindex_file(file_path, rel_path, content_hash, stat)
                    stats.changed += 1
                    stats.extracted += 1
                    logger.info("Changed: %s", rel_path)
                else:
                    stats.skipped += 1

            except (PermissionError, OSError) as e:
                stats.error += 1
                logger.warning("Cannot read %s: %s", file_path, e)

    # Detect deleted files
    for db_path in existing_db_paths:
        if db_path not in found_paths:
            all_docs = list_documents()
            for d in all_docs:
                if d.path == db_path:
                    delete_chunks_for_document(d.id)
                    delete_document(d.id)
                    stats.deleted += 1
                    logger.info("Deleted: %s", db_path)
                    break

    # Build embeddings if there are new or changed files
    if stats.new > 0 or stats.changed > 0:
        _build_embeddings()

    return stats


def _index_and_extract(
    file_path: Path,
    rel_path: str,
    content_hash: str,
    stat: os.stat_result,
) -> None:
    """Index a file and extract its content into chunks."""
    doc = Document(
        id=content_hash[:16],
        path=rel_path,
        name=file_path.name,
        extension=file_path.suffix.lower(),
        mime_type=_guess_mime(file_path),
        size=stat.st_size,
        content_hash=content_hash,
        created_at=datetime.fromtimestamp(stat.st_ctime),
        modified_at=datetime.fromtimestamp(stat.st_mtime),
    )
    insert_document(doc)

    # Extract content
    try:
        extracted = extract_file(file_path)
        if extracted and extracted.chunks:
            for i, exc_chunk in enumerate(extracted.chunks):
                chunk_id = f"{doc.id}_{i:04d}"
                chunk = Chunk(
                    id=chunk_id,
                    document_id=doc.id,
                    text=exc_chunk.text,
                    start_offset=exc_chunk.start_offset,
                    end_offset=exc_chunk.end_offset,
                    page=exc_chunk.page,
                    section=exc_chunk.section,
                )
                insert_chunk(chunk)
            logger.info("Extracted %d chunks from %s", len(extracted.chunks), rel_path)
    except Exception as e:
        logger.error("Extraction failed for %s: %s", rel_path, e)


def _reindex_file(
    file_path: Path,
    rel_path: str,
    content_hash: str,
    stat: os.stat_result,
) -> None:
    """Re-index a changed file: update doc and re-extract chunks."""
    doc = Document(
        id=content_hash[:16],
        path=rel_path,
        name=file_path.name,
        extension=file_path.suffix.lower(),
        mime_type=_guess_mime(file_path),
        size=stat.st_size,
        content_hash=content_hash,
        created_at=datetime.fromtimestamp(stat.st_ctime),
        modified_at=datetime.fromtimestamp(stat.st_mtime),
    )
    insert_document(doc)

    # Delete old chunks and re-extract
    delete_chunks_for_document(doc.id)

    try:
        extracted = extract_file(file_path)
        if extracted and extracted.chunks:
            for i, exc_chunk in enumerate(extracted.chunks):
                chunk_id = f"{doc.id}_{i:04d}"
                chunk = Chunk(
                    id=chunk_id,
                    document_id=doc.id,
                    text=exc_chunk.text,
                    start_offset=exc_chunk.start_offset,
                    end_offset=exc_chunk.end_offset,
                    page=exc_chunk.page,
                    section=exc_chunk.section,
                )
                insert_chunk(chunk)
    except Exception as e:
        logger.error("Re-extraction failed for %s: %s", rel_path, e)


def _guess_mime(path: Path) -> str:
    ext = path.suffix.lower()
    mime_map = {
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".py": "text/x-python",
        ".js": "text/javascript",
        ".ts": "text/typescript",
        ".jsx": "text/javascript",
        ".tsx": "text/typescript",
        ".java": "text/x-java",
        ".c": "text/x-c",
        ".cpp": "text/x-c++",
        ".h": "text/x-c",
        ".hpp": "text/x-c++",
        ".cs": "text/x-csharp",
        ".go": "text/x-go",
        ".rs": "text/x-rust",
        ".rb": "text/x-ruby",
        ".php": "text/x-php",
        ".swift": "text/x-swift",
        ".kt": "text/x-kotlin",
        ".json": "application/json",
        ".yaml": "text/yaml",
        ".yml": "text/yaml",
        ".toml": "text/toml",
        ".csv": "text/csv",
        ".html": "text/html",
        ".htm": "text/html",
        ".css": "text/css",
        ".xml": "text/xml",
        ".sql": "text/x-sql",
        ".sh": "text/x-shellscript",
        ".bash": "text/x-shellscript",
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".bmp": "image/bmp",
        ".gif": "image/gif",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
        ".webp": "image/webp",
    }
    return mime_map.get(ext, "application/octet-stream")


def _build_embeddings() -> None:
    """Build embeddings for all chunks and update FAISS index."""
    try:
        from app.embeddings.local import LocalEmbedding
        from app.vectorstore.faiss_store import FAISSStore
        from app.database.repositories import get_all_chunks

        embedding = LocalEmbedding()
        store = FAISSStore()

        chunks = get_all_chunks()
        if not chunks:
            return

        # Filter chunks that don't have embeddings yet
        texts = []
        chunk_ids = []
        for chunk in chunks:
            # Simple: embed all chunks (cache handles duplicates)
            texts.append(chunk.text)
            chunk_ids.append(chunk.id)

        if not texts:
            return

        logger.info("Building embeddings for %d chunks...", len(texts))
        vectors = embedding.embed(texts)

        # Build or update FAISS index
        if store.count() == 0:
            store.build(vectors, chunk_ids)
        else:
            # For simplicity, rebuild entirely (proper solution would diff)
            store.build(vectors, chunk_ids)

        logger.info("FAISS index updated: %d vectors", store.count())

    except ImportError as e:
        logger.warning("Embedding dependencies not available: %s", e)
    except Exception as e:
        logger.error("Failed to build embeddings: %s", e)
