from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.config.settings import LifeOSSettings
from app.models.search import SearchResult


def rank_results(
    results: list[SearchResult],
    settings: LifeOSSettings,
) -> list[SearchResult]:
    """Re-rank search results using hybrid scoring.

    final_score =
        semantic_weight * semantic_score
      + keyword_weight * keyword_score
      + recency_weight * recency_score
      + metadata_weight * metadata_score
    """
    if not results:
        return results

    max_score = max(r.score for r in results) or 1.0

    for r in results:
        # Normalize semantic score
        normalized_semantic = r.score / max_score

        # Keyword score: boost if query words appear in snippet
        keyword_boost = 0.0
        snippet_lower = r.snippet.lower() if r.snippet else ""
        # Common keywords to boost
        boost_words = ["öğrenci", "numara", "no", "t.c.", "kimlik", "sgk", "belge", "transkript"]
        for word in boost_words:
            if word in snippet_lower:
                keyword_boost = max(keyword_boost, 0.5)
                break

        # Recency score: boost for recently modified files
        recency_score = 0.5  # default
        if r.modified_at:
            try:
                mod_date = datetime.fromisoformat(r.modified_at)
                days_ago = (datetime.utcnow() - mod_date).days
                recency_score = max(0.0, 1.0 - (days_ago / 365))
            except Exception:
                pass

        # Metadata score: boost for matches in section/page
        metadata_score = 0.0
        if r.section:
            metadata_score = 0.3
        if r.page:
            metadata_score = 0.2

        r.score = (
            settings.semantic_weight * normalized_semantic
            + settings.keyword_weight * keyword_boost
            + settings.recency_weight * recency_score
            + settings.metadata_weight * metadata_score
        )

    results.sort(key=lambda r: r.score, reverse=True)
    return results
