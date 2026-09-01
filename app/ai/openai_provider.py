from __future__ import annotations

import os
import logging
import requests

from app.ai.base import AIRequest, AIResponse, register_provider
from app.ai.prompts import SYSTEM_PROMPT, build_rag_prompt_with_history

logger = logging.getLogger(__name__)

OPENAI_MODELS = {
    "gpt-4o": {"context": 128000, "cost": "high", "quality": "best"},
    "gpt-4o-mini": {"context": 128000, "cost": "low", "quality": "good"},
    "gpt-4-turbo": {"context": 128000, "cost": "medium", "quality": "best"},
    "o1": {"context": 128000, "cost": "high", "quality": "best"},
    "o3": {"context": 200000, "cost": "high", "quality": "best"},
}


class OpenAIProvider:
    """OpenAI API provider using REST directly (no SDK dependency)."""

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

    def generate(self, request: AIRequest) -> AIResponse:
        if not self._api_key:
            return AIResponse(
                answer="OpenAI API key not configured. Set OPENAI_API_KEY in .env",
                model=self._model,
                provider="openai",
            )

        try:
            user_prompt = build_rag_prompt_with_history(
                question=request.question,
                context=request.context,
                chat_history=request.chat_history,
            )

            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": request.max_tokens,
                "temperature": 0.3,
            }

            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()

            answer = data["choices"][0]["message"]["content"]
            usage = {}
            if "usage" in data:
                usage = {
                    "prompt_tokens": data["usage"].get("prompt_tokens", 0),
                    "completion_tokens": data["usage"].get("completion_tokens", 0),
                    "total_tokens": data["usage"].get("total_tokens", 0),
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

        except requests.exceptions.RequestException as e:
            logger.error("OpenAI API error: %s", e)
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    err_data = e.response.json()
                    if "error" in err_data:
                        error_msg = err_data["error"].get("message", str(e))
                except Exception:
                    pass
            return AIResponse(
                answer=f"OpenAI error: {error_msg}",
                model=self._model,
                provider="openai",
            )
        except Exception as e:
            logger.error("OpenAI error: %s", e)
            return AIResponse(
                answer=f"OpenAI error: {str(e)}",
                model=self._model,
                provider="openai",
            )

    def list_models(self) -> list[str]:
        return list(OPENAI_MODELS.keys())


# Register provider
register_provider("openai", OpenAIProvider)
