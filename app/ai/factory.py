from __future__ import annotations

import os

from app.ai.base import get_provider, list_providers, AIProvider

import logging

logger = logging.getLogger(__name__)


def get_ai_provider(
    provider: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
) -> AIProvider:
    """Get the best available AI provider.

    Priority:
    1. Explicit provider name
    2. LIFEOS_AI_PROVIDER env var
    3. Auto-detect (try openai, then gemini)
    """
    # Ensure providers are registered
    _ensure_providers()

    name = provider or os.getenv("LIFEOS_AI_PROVIDER", "auto")
    return get_provider(name=name, api_key=api_key, model=model)


def _ensure_providers():
    """Import providers to trigger registration."""
    try:
        from app.ai import openai_provider  # noqa: F401
    except Exception:
        pass

    try:
        from app.ai import gemini_provider  # noqa: F401
    except Exception:
        pass


def get_provider_info() -> list[dict]:
    """Get info about all available providers."""
    _ensure_providers()

    providers = []
    for name in list_providers():
        try:
            p = get_provider(name)
            providers.append({
                "name": name,
                "available": p.available,
                "models": p.list_models(),
            })
        except Exception:
            providers.append({
                "name": name,
                "available": False,
                "models": [],
            })

    return providers
