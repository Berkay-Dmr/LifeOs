from __future__ import annotations

import re
from typing import Literal

from app.search.global_search import global_search, SearchResult
from app.database.sqlite import get_connection

import logging

logger = logging.getLogger(__name__)

IntentType = Literal["bug", "decision", "memory", "task", "code", "general"]


def detect_intent(question: str) -> IntentType:
    """Detect the intent of a question."""
    q = question.lower()

    # Bug patterns
    bug_patterns = [
        r"error", r"bug", r"crash", r"fail", r"broken", r"issue",
        r"hata", r"sorun", r"çökme", r"bozuk", r"problem",
        r"neden.*çalışmıyor", r"neden.*hata",
    ]
    if any(re.search(p, q) for p in bug_patterns):
        return "bug"

    # Decision patterns
    decision_patterns = [
        r"why.*choose", r"why.*use", r"why.*switch",
        r"decision", r"karar", r"neden.*kullan", r"neden.*seç",
        r"tercih", r"alternatif",
    ]
    if any(re.search(p, q) for p in decision_patterns):
        return "decision"

    # Memory patterns
    memory_patterns = [
        r"when.*did", r"what.*happened", r"remember",
        r"ne zaman", r"ne oldu", r"hatırla", r"geçenlerde",
    ]
    if any(re.search(p, q) for p in memory_patterns):
        return "memory"

    # Task patterns
    task_patterns = [
        r"todo", r"task", r"need to", r"should.*do",
        r"görev", r"yapmam lazım", r"yapılacak",
    ]
    if any(re.search(p, q) for p in task_patterns):
        return "task"

    # Code patterns
    code_patterns = [
        r"function", r"class", r"import", r"call",
        r"fonksiyon", r"sınıf", r"nerede.*kullan", r"bağımlılık",
    ]
    if any(re.search(p, q) for p in code_patterns):
        return "code"

    return "general"


def build_smart_context(question: str, max_chunks: int = 8) -> str:
    """Build context based on question intent."""
    intent = detect_intent(question)

    # Get results from global search
    all_results = global_search(question, limit=20)

    # Prioritize based on intent
    context_parts = []

    if intent == "bug":
        # Bugs first, then code, then commits
        context_parts.extend(_format_results(all_results.get("bugs", [])[:3], "Bug"))
        context_parts.extend(_format_results(all_results.get("code", [])[:2], "Code"))
        context_parts.extend(_format_results(all_results.get("commits", [])[:2], "Commit"))

    elif intent == "decision":
        # Decisions first, then memory, then commits
        context_parts.extend(_format_results(all_results.get("decisions", [])[:3], "Decision"))
        context_parts.extend(_format_results(all_results.get("memory", [])[:2], "Memory"))
        context_parts.extend(_format_results(all_results.get("commits", [])[:2], "Commit"))

    elif intent == "memory":
        # Memory first, then commits, then files
        context_parts.extend(_format_results(all_results.get("memory", [])[:3], "Memory"))
        context_parts.extend(_format_results(all_results.get("commits", [])[:2], "Commit"))
        context_parts.extend(_format_results(all_results.get("files", [])[:2], "File"))

    elif intent == "task":
        # Tasks first, then files
        context_parts.extend(_format_results(all_results.get("tasks", [])[:3], "Task"))
        context_parts.extend(_format_results(all_results.get("files", [])[:2], "File"))

    elif intent == "code":
        # Code first, then files
        context_parts.extend(_format_results(all_results.get("code", [])[:3], "Code"))
        context_parts.extend(_format_results(all_results.get("files", [])[:2], "File"))

    else:
        # General: mix of everything
        context_parts.extend(_format_results(all_results.get("files", [])[:2], "File"))
        context_parts.extend(_format_results(all_results.get("code", [])[:2], "Code"))
        context_parts.extend(_format_results(all_results.get("commits", [])[:2], "Commit"))
        context_parts.extend(_format_results(all_results.get("memory", [])[:1], "Memory"))

    # Also get semantic search results from chunks
    try:
        from app.search.hybrid import hybrid_search
        from app.models.search import SearchQuery

        sq = SearchQuery(text=question, top_k=max_chunks)
        from app.config.settings import get_settings
        settings = get_settings()
        chunk_results = hybrid_search(sq, settings)

        if chunk_results:
            context_parts.append("\n=== Document Chunks ===")
            for i, r in enumerate(chunk_results[:max_chunks], 1):
                context_parts.append(f"\n[{i}] {r.path}")
                if r.snippet:
                    context_parts.append(r.snippet[:500])
    except Exception as e:
        logger.debug("Chunk search failed: %s", e)

    return "\n".join(context_parts)


def _format_results(results: list[SearchResult], category: str) -> list[str]:
    """Format search results for context."""
    if not results:
        return []

    parts = [f"\n=== {category}s ==="]

    for i, r in enumerate(results, 1):
        parts.append(f"\n[{i}] {r.title}")
        if r.snippet:
            parts.append(f"    {r.snippet[:200]}")
        if r.source:
            parts.append(f"    Source: {r.source}")

    return parts


def build_answer_with_sources(question: str, answer_text: str) -> dict:
    """Build a structured answer with sources."""
    intent = detect_intent(question)
    all_results = global_search(question, limit=10)

    sources = []

    # Collect relevant sources
    for result_type in ["files", "bugs", "decisions", "memory", "commits", "code", "tasks"]:
        for r in all_results.get(result_type, [])[:3]:
            sources.append({
                "type": r.type,
                "title": r.title,
                "source": r.source,
                "snippet": r.snippet[:100] if r.snippet else "",
            })

    return {
        "answer": answer_text,
        "intent": intent,
        "sources": sources[:10],
    }
