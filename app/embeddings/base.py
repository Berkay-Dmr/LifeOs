from __future__ import annotations

from typing import Protocol


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...
    def embed_single(self, text: str) -> list[float]: ...
    @property
    def dimension(self) -> int: ...
