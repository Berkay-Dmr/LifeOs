from __future__ import annotations

import os
import logging

from app.ai.base import AIRequest, AIResponse, register_provider
from app.ai.prompts import SYSTEM_PROMPT, build_rag_prompt_with_history

logger = logging.getLogger(__name__)

GEMINI_MODELS = {
    # Gemini 2.5
    "gemini-2.5-pro": {"context": 1000000, "cost": "medium", "quality": "best"},
    "gemini-2.5-flash": {"context": 1000000, "cost": "low", "quality": "good"},
    "gemini-2.5-pro-preview-05-06": {"context": 1000000, "cost": "medium", "quality": "best"},
    "gemini-2.5-flash-preview-04-17": {"context": 1000000, "cost": "low", "quality": "good"},
    # Gemini 2.0
    "gemini-2.0-flash": {"context": 1000000, "cost": "low", "quality": "good"},
    "gemini-2.0-flash-lite": {"context": 1000000, "cost": "low", "quality": "good"},
    # Gemini 1.5
    "gemini-1.5-pro": {"context": 2000000, "cost": "medium", "quality": "best"},
    "gemini-1.5-flash": {"context": 1000000, "cost": "low", "quality": "good"},
    "gemini-1.5-flash-8b": {"context": 1000000, "cost": "low", "quality": "good"},
}


class GeminiProvider:
    """Google Gemini API provider."""

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

    def list_models(self) -> list[str]:
        return list(GEMINI_MODELS.keys())

    def generate(self, request: AIRequest) -> AIResponse:
        if not self._api_key:
            return AIResponse(
                answer="Gemini API key not configured. Set GEMINI_API_KEY.",
                model=self._model,
                provider="gemini",
            )

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self._api_key)

            user_prompt = build_rag_prompt_with_history(
                question=request.question,
                context=request.context,
                chat_history=request.chat_history,
            )

            # Use Chat API to avoid AFC warning
            chat = client.chats.create(model=self._model)
            response = chat.send_message(
                user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=request.max_tokens,
                    temperature=0.3,
                ),
            )

            answer = response.text or ""
            usage = {}
            if response.usage_metadata:
                usage = {
                    "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                    "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
                    "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
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

        except ImportError:
            return AIResponse(
                answer="Google GenAI library not installed. Run: pip install google-genai",
                model=self._model,
                provider="gemini",
            )
        except Exception as e:
            logger.error("Gemini API error: %s", e)
            return AIResponse(
                answer=f"Gemini error: {str(e)}",
                model=self._model,
                provider="gemini",
            )


# Register provider
register_provider("gemini", GeminiProvider)
