from __future__ import annotations

from datetime import datetime

from app.config.settings import LifeOSSettings
from app.models.search import SearchResult


def rank_results(
    results: list[SearchResult],
    settings: LifeOSSettings,
) -> list[SearchResult]:
    """Re-rank search results with diversity, dedup, and quality scoring.

    Scoring factors:
    1. Relevance (original score)
    2. Keyword density (how many query words appear)
    3. Chunk quality (length, has section/page info)
    4. Document diversity (penalize multiple chunks from same doc)
    5. Recency (newer files get slight boost)
    """
    if not results:
        return results

    # Step 1: Deduplicate similar snippets
    results = _deduplicate_snippets(results)

    # Step 2: Calculate enhanced scores
    max_score = max(r.score for r in results) or 1.0
    doc_counts: dict[str, int] = {}

    for r in results:
        # Base relevance
        normalized = r.score / max_score

        # Keyword density
        snippet_lower = r.snippet.lower() if r.snippet else ""
        keyword_score = _keyword_density(snippet_lower)

        # Chunk quality
        quality_score = _chunk_quality(r)

        # Document diversity penalty
        doc_id = r.document_id
        doc_counts[doc_id] = doc_counts.get(doc_id, 0) + 1
        diversity_penalty = 1.0 / (1.0 + (doc_counts[doc_id] - 1) * 0.3)

        # Recency
        recency = _recency_score(r)

        # Final score
        r.score = (
            0.40 * normalized        # Relevance
            + 0.25 * keyword_score   # Keyword density
            + 0.15 * quality_score   # Chunk quality
            + 0.10 * diversity_penalty  # Diversity
            + 0.10 * recency         # Recency
        )

    results.sort(key=lambda r: r.score, reverse=True)
    return results


def _deduplicate_snippets(results: list[SearchResult]) -> list[SearchResult]:
    """Remove near-duplicate snippets."""
    seen_texts: set[str] = set()
    unique: list[SearchResult] = []

    for r in results:
        # Normalize text for comparison
        text = (r.snippet or "").lower().strip()
        # Use first 100 chars as dedup key
        key = text[:100]

        if key not in seen_texts:
            seen_texts.add(key)
            unique.append(r)

    return unique


def _keyword_density(text: str) -> float:
    """Calculate how many meaningful keywords appear in text."""
    if not text:
        return 0.0

    # High-value keywords
    important_words = [
        "öğrenci", "numara", "no", "t.c.", "kimlik", "sgk", "belge",
        "transkript", "üniversite", "fakülte", "bölüm", "program",
        "borç", "prim", "sicil", "adli", "mezun", "aktif", "KYK",
        "burs", "kredi", "barınma", "yurt",
    ]

    matches = sum(1 for word in important_words if word in text)
    return min(matches / 3.0, 1.0)  # Cap at 1.0


def _chunk_quality(r: SearchResult) -> float:
    """Score chunk quality based on length and metadata."""
    score = 0.0

    # Length bonus (prefer substantive chunks)
    snippet_len = len(r.snippet or "")
    if snippet_len > 100:
        score += 0.3
    if snippet_len > 200:
        score += 0.2

    # Metadata bonus
    if r.page:
        score += 0.2
    if r.section:
        score += 0.2

    # Has actual content (not just file reference)
    if r.snippet and not r.snippet.startswith("[File:"):
        score += 0.1

    return min(score, 1.0)


def _recency_score(r: SearchResult) -> float:
    """Boost recently modified files."""
    if not r.modified_at:
        return 0.5

    try:
        mod_date = datetime.fromisoformat(r.modified_at)
        days_ago = (datetime.utcnow() - mod_date).days
        # Linear decay over 1 year
        return max(0.2, 1.0 - (days_ago / 365))
    except Exception:
        return 0.5
