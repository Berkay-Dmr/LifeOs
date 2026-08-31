from __future__ import annotations

import os
import logging

from app.ai.base import AIRequest, AIResponse, register_provider
from app.ai.prompts import SYSTEM_PROMPT, build_rag_prompt_with_history

logger = logging.getLogger(__name__)

OPENAI_MODELS = {
    # GPT-4o models
    "gpt-4o": {"context": 128000, "cost": "high", "quality": "best"},
    "gpt-4o-mini": {"context": 128000, "cost": "low", "quality": "good"},
    "gpt-4o-2024-05-13": {"context": 128000, "cost": "high", "quality": "best"},
    "gpt-4o-2024-08-06": {"context": 128000, "cost": "high", "quality": "best"},
    "gpt-4o-2024-11-20": {"context": 128000, "cost": "high", "quality": "best"},
    # GPT-4o mini
    "gpt-4o-mini-2024-07-18": {"context": 128000, "cost": "low", "quality": "good"},
    # GPT-4 Turbo
    "gpt-4-turbo": {"context": 128000, "cost": "high", "quality": "best"},
    "gpt-4-turbo-2024-04-09": {"context": 128000, "cost": "high", "quality": "best"},
    # GPT-4
    "gpt-4": {"context": 8192, "cost": "high", "quality": "best"},
    "gpt-4-32k": {"context": 32768, "cost": "high", "quality": "best"},
    # GPT-3.5
    "gpt-3.5-turbo": {"context": 16385, "cost": "low", "quality": "good"},
    "gpt-3.5-turbo-16k": {"context": 16385, "cost": "low", "quality": "good"},
    # o1 reasoning models
    "o1": {"context": 200000, "cost": "high", "quality": "best"},
    "o1-mini": {"context": 128000, "cost": "medium", "quality": "good"},
    "o1-2024-12-17": {"context": 200000, "cost": "high", "quality": "best"},
    # o3 reasoning models
    "o3": {"context": 200000, "cost": "high", "quality": "best"},
    "o3-mini": {"context": 200000, "cost": "medium", "quality": "good"},
    "o3-mini-2025-01-31": {"context": 200000, "cost": "medium", "quality": "good"},
}


class OpenAIProvider:
    """OpenAI API provider with support for all models."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        from app.config.settings import get_settings
        settings = get_settings()
        self._api_key = api_key or settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")
        self._model = model or settings.openai_model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    @property
    def name(self) -> str:
        return "openai"

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    def list_models(self) -> list[str]:
        return list(OPENAI_MODELS.keys())

    def generate(self, request: AIRequest) -> AIResponse:
        if not self._api_key:
            return AIResponse(
                answer="OpenAI API key not configured. Set OPENAI_API_KEY.",
                model=self._model,
                provider="openai",
            )

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self._api_key)

            user_prompt = build_rag_prompt_with_history(
                question=request.question,
                context=request.context,
                chat_history=request.chat_history,
            )

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]

            # o1/o3 models don't support system message or temperature
            if self._model.startswith("o1") or self._model.startswith("o3"):
                messages = [{"role": "user", "content": user_prompt}]
                response = client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    max_tokens=request.max_tokens,
                )
            else:
                response = client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    max_tokens=request.max_tokens,
                    temperature=0.3,
                )

            answer = response.choices[0].message.content or ""
            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            logger.info(
                "OpenAI response: %d tokens, model=%s",
                usage.get("total_tokens", 0),
                self._model,
            )

            return AIResponse(
                answer=answer,
                model=self._model,
                provider="openai",
                usage=usage,
            )

        except ImportError:
            return AIResponse(
                answer="OpenAI library not installed. Run: pip install openai",
                model=self._model,
                provider="openai",
            )
        except Exception as e:
            logger.error("OpenAI API error: %s", e)
            return AIResponse(
                answer=f"OpenAI error: {str(e)}",
                model=self._model,
                provider="openai",
            )


# Register provider
register_provider("openai", OpenAIProvider)
