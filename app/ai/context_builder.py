from __future__ import annotations

from app.models.search import SearchResult


def build_context(
    results: list[SearchResult],
    max_chunks: int = 8,
) -> str:
    """Build context string from search results for AI."""
    if not results:
        return ""

    parts: list[str] = []
    for i, r in enumerate(results[:max_chunks], 1):
        source_ref = f"[{i}] {r.path}"
        if r.page:
            source_ref += f" (sayfa {r.page})"
        if r.section:
            source_ref += f" — {r.section}"

        parts.append(f"{source_ref}\n{r.snippet}")

    return "\n\n---\n\n".join(parts)


def extract_source_references(results: list[SearchResult]) -> list[str]:
    """Extract human-readable source references."""
    refs: list[str] = []
    for i, r in enumerate(results, 1):
        ref = f"[{i}] {r.path}"
        if r.page:
            ref += f" (sayfa {r.page})"
        if r.section:
            ref += f" — {r.section}"
        refs.append(ref)
    return refs
