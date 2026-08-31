from __future__ import annotations

import re


def truncate(text: str, max_length: int = 200) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def clean_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def count_tokens_approx(text: str) -> int:
    """Rough token count: ~4 chars per token for English."""
    return len(text) // 4
