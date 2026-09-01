from __future__ import annotations

from app.config.settings import LifeOSSettings
from app.models.search import SearchQuery, SearchResult
from app.search.ranking import rank_results

import logging

logger = logging.getLogger(__name__)

# Query expansion synonyms
SYNONYM_MAP: dict[str, list[str]] = {
    "numara": ["no", "numara", "numarası", "numaram"],
    "öğrenci": ["öğrenci", "ogrenci", "öğrenci"],
    "belge": ["belge", "belgesi", "doküman"],
    "üniversite": ["üniversite", "niversite", "yükseköğretim"],
    "fakülte": ["fakülte", "fakulte"],
    "borç": ["borç", "alacak", "prim"],
    "sicil": ["sicil", "kayıt", "adli"],
    "mezun": ["mezun", "bitirme", "diploma"],
    "barınma": ["barınma", "yurt", "konaklama"],
    "burs": ["burs", "kredi", " KYK"],
}


def expand_query(text: str) -> list[str]:
    """Expand query with synonyms for better recall."""
    words = text.lower().split()
    expanded = [text]  # Original query first

    for word in words:
        for key, synonyms in SYNONYM_MAP.items():
            if word in synonyms or any(s in word for s in synonyms):
                # Add synonym-expanded version
                for syn in synonyms:
                    if syn != word:
                        expanded_text = text.lower().replace(word, syn)
                        if expanded_text not in expanded:
                            expanded.append(expanded_text)
                break

    return expanded[:5]  # Limit expansions


def hybrid_search(query: SearchQuery, settings: LifeOSSettings) -> list[SearchResult]:
    """Hybrid search: semantic + keyword + ranking."""
    results: list[SearchResult] = []
    seen: set[str] = set()

    # File type filter extensions
    file_type_map = {
        "pdf": [".pdf"],
        "doc": [".docx", ".doc", ".txt", ".md", ".rtf"],
        "code": [".py", ".js", ".ts", ".java", ".c", ".cpp", ".cs", ".go", ".rs", ".rb", ".php", ".html", ".css", ".json", ".yaml", ".yml", ".toml"],
        "image": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"],
    }
    filter_exts = None
    if query.file_type and query.file_type in file_type_map:
        filter_exts = file_type_map[query.file_type]

    def _matches_filter(doc_path: str) -> bool:
        if not filter_exts:
            return True
        path_lower = doc_path.lower()
        return any(path_lower.endswith(ext) for ext in filter_exts)

    # 1. Semantic search with query expansion
    try:
        from app.search.semantic import semantic_search
        expanded_queries = expand_query(query.text)

        for expanded in expanded_queries:
            semantic_results = semantic_search(
                expanded, top_k=query.top_k, settings=settings
            )
            for r in semantic_results:
                if not _matches_filter(r.path):
                    continue
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
                if doc and _matches_filter(doc.path):
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
                if not _matches_filter(doc.path):
                    continue
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
