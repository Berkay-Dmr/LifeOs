from __future__ import annotations

import re

from app.ai.base import AIResponse
from app.models.search import SearchResult


def validate_answer(
    response: AIResponse,
    results: list[SearchResult],
) -> AIResponse:
    """Validate AI response for hallucination and quality.

    Checks:
    1. Is the answer empty?
    2. Does it reference sources?
    3. Is it too short?
    """
    answer = response.answer.strip()

    # Empty answer
    if not answer:
        response.answer = (
            "Bu konuda indekslenmiş yeterli bilgi bulamadım."
        )
        return response

    # Too short (likely a refusal or error)
    if len(answer) < 20 and not results:
        return response

    # Check if sources were cited
    source_pattern = r"\[\d+\]"
    cited = re.findall(source_pattern, answer)

    # If we have search results but no citations, add source list
    if results and not cited:
        source_list = "\n\nKaynaklar:\n"
        for i, r in enumerate(results[:5], 1):
            ref = f"[{i}] {r.path}"
            if r.page:
                ref += f" (sayfa {r.page})"
            source_list += f"  {ref}\n"
        response.answer += source_list

    return response
