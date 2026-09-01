from __future__ import annotations

import os
import json
import logging
import requests

from app.ai.base import AIRequest, AIResponse, register_provider
from app.ai.prompts import SYSTEM_PROMPT, build_rag_prompt_with_history

logger = logging.getLogger(__name__)

GEMINI_MODELS = {
    "gemini-2.5-flash": {"context": 1000000, "cost": "low", "quality": "good"},
    "gemini-2.5-pro": {"context": 1000000, "cost": "medium", "quality": "best"},
    "gemini-2.0-flash": {"context": 1000000, "cost": "low", "quality": "good"},
    "gemini-1.5-flash": {"context": 1000000, "cost": "low", "quality": "good"},
    "gemini-1.5-pro": {"context": 2000000, "cost": "medium", "quality": "best"},
}


class GeminiProvider:
    """Google Gemini API provider using REST directly (no SDK dependency)."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        from app.config.settings import get_settings
        settings = get_settings()
        self._api_key = api_key or settings.gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self._model = model or settings.gemini_model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    def generate(self, request: AIRequest) -> AIResponse:
        if not self._api_key:
            return AIResponse(
                answer="Gemini API key not configured. Set GEMINI_API_KEY in .env",
                model=self._model,
                provider="gemini",
            )

        try:
            user_prompt = build_rag_prompt_with_history(
                question=request.question,
                context=request.context,
                chat_history=request.chat_history,
            )

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent?key={self._api_key}"

            payload = {
                "system_instruction": {
                    "parts": [{"text": SYSTEM_PROMPT}]
                },
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": user_prompt}]
                    }
                ],
                "generationConfig": {
                    "maxOutputTokens": request.max_tokens,
                    "temperature": 0.3,
                }
            }

            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()

            # Extract answer
            answer = ""
            if "candidates" in data and data["candidates"]:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    answer = "".join(p.get("text", "") for p in parts)

            # Extract usage
            usage = {}
            if "usageMetadata" in data:
                um = data["usageMetadata"]
                usage = {
                    "prompt_tokens": um.get("promptTokenCount", 0),
                    "completion_tokens": um.get("candidatesTokenCount", 0),
                    "total_tokens": um.get("totalTokenCount", 0),
                }

            logger.info(
                "Gemini response: %d tokens, model=%s",
                usage.get("total_tokens", 0),
                self._model,
            )

            return AIResponse(
                answer=answer,
                model=self._model,
                provider="gemini",
                usage=usage,
            )

        except requests.exceptions.RequestException as e:
            logger.error("Gemini API error: %s", e)
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    err_data = e.response.json()
                    if "error" in err_data:
                        error_msg = err_data["error"].get("message", str(e))
                except Exception:
                    pass
            return AIResponse(
                answer=f"Gemini error: {error_msg}",
                model=self._model,
                provider="gemini",
            )
        except Exception as e:
            logger.error("Gemini error: %s", e)
            return AIResponse(
                answer=f"Gemini error: {str(e)}",
                model=self._model,
                provider="gemini",
            )

    def list_models(self) -> list[str]:
        return list(GEMINI_MODELS.keys())


# Register provider
register_provider("gemini", GeminiProvider)
