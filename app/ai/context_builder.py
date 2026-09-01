from __future__ import annotations

from app.models.search import SearchResult


def build_context(
    results: list[SearchResult],
    max_chunks: int = 8,
) -> str:
    """Build context string from search results for AI.

    Improvements over basic version:
    1. Groups chunks by document for better coherence
    2. Truncates very long snippets
    3. Adds relevance indicator
    4. Better formatting
    """
    if not results:
        return ""

    # Group by document
    doc_groups: dict[str, list[tuple[int, SearchResult]]] = {}
    for i, r in enumerate(results[:max_chunks]):
        doc_key = r.path
        if doc_key not in doc_groups:
            doc_groups[doc_key] = []
        doc_groups[doc_key].append((i + 1, r))

    parts: list[str] = []

    for doc_path, chunks in doc_groups.items():
        # Document header
        doc_header = f"=== {doc_path} ==="
        if len(chunks) > 1:
            doc_header += f" ({len(chunks)} sections)"
        parts.append(doc_header)

        # Chunks within this document
        for idx, r in chunks:
            source_ref = f"[{idx}]"
            if r.page:
                source_ref += f" Sayfa {r.page}"
            if r.section:
                source_ref += f" — {r.section}"

            # Truncate long snippets
            snippet = r.snippet or ""
            if len(snippet) > 500:
                snippet = snippet[:497] + "..."

            # Relevance indicator
            relevance = "yüksek" if r.score > 0.6 else "orta" if r.score > 0.4 else "düşük"

            parts.append(f"{source_ref} (ilgi: {relevance})\n{snippet}")

        parts.append("")  # Empty line between documents

    return "\n".join(parts)


def extract_source_references(results: list[SearchResult]) -> list[str]:
    """Extract human-readable source references."""
    refs: list[str] = []
    seen_paths: set[str] = set()

    for i, r in enumerate(results, 1):
        # Deduplicate by path
        if r.path in seen_paths:
            continue
        seen_paths.add(r.path)

        ref = f"[{i}] {r.path}"
        if r.page:
            ref += f" (sayfa {r.page})"
        refs.append(ref)

    return refs
