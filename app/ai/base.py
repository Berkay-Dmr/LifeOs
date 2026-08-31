from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class AIRequest:
    question: str
    context: str
    chat_history: list[dict[str, str]] = field(default_factory=list)
    max_tokens: int = 1024


@dataclass
class AIResponse:
    answer: str
    sources: list[str] = field(default_factory=list)
    model: str = ""
    provider: str = ""
    usage: dict[str, int] = field(default_factory=dict)


class AIProvider(Protocol):
    """Protocol for AI providers."""

    @property
    def name(self) -> str: ...

    @property
    def available(self) -> bool: ...

    def generate(self, request: AIRequest) -> AIResponse: ...

    def list_models(self) -> list[str]: ...


# Provider registry
_providers: dict[str, type] = {}


def register_provider(name: str, cls: type) -> None:
    _providers[name] = cls


def get_provider(name: str | None = None, api_key: str | None = None, model: str | None = None):
    """Get an AI provider by name. If name is None, auto-detect."""
    if name is None or name == "auto":
        # Try providers in order
        for pname in ["openai", "gemini"]:
            if pname in _providers:
                cls = _providers[pname]
                try:
                    provider = cls(api_key=api_key, model=model) if api_key else cls()
                    if provider.available:
                        return provider
                except Exception:
                    continue
        raise RuntimeError("No AI provider available. Set OPENAI_API_KEY or GEMINI_API_KEY.")

    if name not in _providers:
        raise ValueError(f"Unknown provider: {name}. Available: {list(_providers.keys())}")

    cls = _providers[name]
    return cls(api_key=api_key, model=model) if api_key else cls()


def list_providers() -> list[str]:
    return list(_providers.keys())
