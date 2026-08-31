from __future__ import annotations

from app.config.settings import LifeOSSettings
from app.models.search import SearchResult
from app.vectorstore.faiss_store import FAISSStore
from app.embeddings.local import LocalEmbedding
from app.database.repositories import get_document_by_id, get_chunks_for_document

import logging

logger = logging.getLogger(__name__)


def semantic_search(
    query: str,
    top_k: int = 10,
    settings: LifeOSSettings | None = None,
) -> list[SearchResult]:
    """Search using semantic similarity via FAISS."""
    from app.config.settings import get_settings
    from app.database.sqlite import init_db

    if settings is None:
        settings = get_settings()
    init_db(settings.db_path)

    store = FAISSStore()
    store._load()

    if store.count() == 0:
        return []

    embedding = LocalEmbedding()
    query_vec = embedding.embed_single(query)

    raw_results = store.search(query_vec, top_k=top_k)

    results: list[SearchResult] = []
    for chunk_id, score in raw_results:
        # Find the document for this chunk
        # chunk_id format: {doc_id}_{index}
        doc_id = chunk_id.split("_")[0] if "_" in chunk_id else chunk_id[:16]
        doc = get_document_by_id(doc_id)
        if doc is None:
            continue

        # Find the specific chunk text
        chunks = get_chunks_for_document(doc_id)
        chunk_text = ""
        page = None
        section = None
        for c in chunks:
            if c.id == chunk_id:
                chunk_text = c.text
                page = c.page
                section = c.section
                break

        if not chunk_text:
            # Fallback: use first chunk
            if chunks:
                chunk_text = chunks[0].text[:200]

        results.append(SearchResult(
            document_id=doc_id,
            chunk_id=chunk_id,
            title=doc.name,
            path=doc.path,
            snippet=chunk_text[:200] if chunk_text else "",
            score=score,
            page=page,
            section=section,
        ))

    return results
