from __future__ import annotations

from app.config.settings import LifeOSSettings
from app.models.search import SearchQuery, SearchResult
from app.search.ranking import rank_results

import logging

logger = logging.getLogger(__name__)


def hybrid_search(query: SearchQuery, settings: LifeOSSettings) -> list[SearchResult]:
    """Hybrid search: semantic + keyword + ranking."""
    results: list[SearchResult] = []
    seen: set[str] = set()

    # 1. Semantic search (if FAISS available)
    try:
        from app.search.semantic import semantic_search
        semantic_results = semantic_search(
            query.text, top_k=query.top_k * 2, settings=settings
        )
        for r in semantic_results:
            key = f"{r.document_id}:{r.chunk_id}"
            if key not in seen:
                seen.add(key)
                results.append(r)
    except Exception as e:
        logger.debug("Semantic search unavailable: %s", e)

    # 2. Keyword search (chunk text) — word-level + partial matching
    try:
        from app.database.repositories import get_all_chunks, get_document_by_id
        import re

        query_lower = query.text.lower()
        # Split query into meaningful words (min 2 chars)
        query_words = [w for w in re.split(r'\W+', query_lower) if len(w) >= 2]

        # Synonyms/partial matches
        synonym_map = {
            "numara": ["no", "numara", "numarası", "numaram"],
            "öğrenci": ["öğrenci", "ogrenci"],
            "belge": ["belge", "belgesi"],
        }

        for chunk in get_all_chunks():
            chunk_lower = chunk.text.lower()

            # Exact substring match (highest score)
            if query_lower in chunk_lower:
                score = 0.7
            else:
                # Check if query words match (with synonyms)
                match_count = 0
                for qw in query_words:
                    # Direct match
                    if qw in chunk_lower:
                        match_count += 1
                        continue
                    # Synonym match
                    for key, synonyms in synonym_map.items():
                        if qw in synonyms or any(s in qw for s in synonyms):
                            if any(s in chunk_lower for s in synonyms):
                                match_count += 1
                                break

                if match_count >= 2:
                    score = 0.6
                elif match_count >= 1 and len(query_words) <= 2:
                    score = 0.5
                else:
                    continue

            key = f"{chunk.document_id}:{chunk.id}"
            if key not in seen:
                seen.add(key)
                doc = get_document_by_id(chunk.document_id)
                if doc:
                    results.append(SearchResult(
                        document_id=chunk.document_id,
                        chunk_id=chunk.id,
                        title=doc.name,
                        path=doc.path,
                        snippet=chunk.text[:200],
                        score=score,
                        page=chunk.page,
                        section=chunk.section,
                    ))
    except Exception as e:
        logger.debug("Keyword search error: %s", e)

    # 3. Keyword search (document name/path fallback)
    if not results:
        try:
            from app.database.repositories import list_documents
            for doc in list_documents():
                score = 0.0
                if query_lower in doc.name.lower():
                    score = 0.6
                elif query_lower in doc.path.lower():
                    score = 0.5
                if score > 0:
                    key = f"{doc.id}:name"
                    if key not in seen:
                        seen.add(key)
                        results.append(SearchResult(
                            document_id=doc.id,
                            chunk_id="",
                            title=doc.name,
                            path=doc.path,
                            snippet=f"[File: {doc.name}]",
                            score=score,
                        ))
        except Exception as e:
            logger.debug("Name search error: %s", e)

    # 4. Rank all results
    results = rank_results(results, settings)

    return results[: query.top_k]
