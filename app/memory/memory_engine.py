from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from app.database.repositories import (
    insert_memory,
    list_memories,
    delete_memory,
    count_memories,
    insert_document,
    get_document_by_id,
)
from app.models.memory import Memory
from app.models.source import Source

import logging

logger = logging.getLogger(__name__)

# Memory types
MEMORY_TYPES = {
    "fact", "preference", "project", "problem",
    "solution", "person", "concept", "event", "decision",
}


class MemoryEngine:
    """Manages long-term memory extraction and retrieval."""

    def create_memory(
        self,
        content: str,
        memory_type: str = "fact",
        confidence: float = 1.0,
        source_doc_ids: list[str] | None = None,
    ) -> Memory:
        """Create and store a new memory."""
        if memory_type not in MEMORY_TYPES:
            memory_type = "fact"

        memory = Memory(
            id=str(uuid.uuid4())[:12],
            type=memory_type,
            content=content,
            confidence=confidence,
            source_count=len(source_doc_ids) if source_doc_ids else 0,
        )
        insert_memory(memory)

        # Link sources
        if source_doc_ids:
            self._link_sources(memory.id, source_doc_ids)

        logger.info("Created memory: %s [%s] (confidence=%.2f)", memory.id, memory_type, confidence)
        return memory

    def recall(self, query: str, top_k: int = 5) -> list[Memory]:
        """Search memories by content similarity."""
        memories = list_memories(active_only=True)
        query_lower = query.lower()

        scored: list[tuple[float, Memory]] = []
        for mem in memories:
            score = 0.0
            content_lower = mem.content.lower()

            # Exact match
            if query_lower in content_lower:
                score = 1.0
            else:
                # Word overlap
                query_words = set(query_lower.split())
                mem_words = set(content_lower.split())
                overlap = query_words & mem_words
                if overlap:
                    score = len(overlap) / max(len(query_words), 1)

            if score > 0:
                scored.append((score * mem.confidence, mem))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [mem for _, mem in scored[:top_k]]

    def forget(self, memory_id: str) -> bool:
        """Deactivate a memory (soft delete)."""
        memories = list_memories(active_only=True)
        for mem in memories:
            if mem.id == memory_id:
                delete_memory(memory_id)
                logger.info("Forgot memory: %s", memory_id)
                return True
        return False

    def list_all(self, active_only: bool = True) -> list[Memory]:
        return list_memories(active_only=active_only)

    def count(self) -> int:
        return count_memories()

    def get_memory(self, memory_id: str) -> Optional[Memory]:
        for mem in list_memories(active_only=False):
            if mem.id == memory_id:
                return mem
        return None

    def _link_sources(self, memory_id: str, doc_ids: list[str]) -> None:
        """Link source documents to a memory."""
        from app.database.sqlite import get_connection

        for doc_id in doc_ids:
            source = Source(
                id=str(uuid.uuid4())[:12],
                memory_id=memory_id,
                document_id=doc_id,
                source_type="document",
            )
            with get_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO sources (id, memory_id, document_id, chunk_id, source_type) VALUES (?, ?, ?, ?, ?)",
                    (source.id, source.memory_id, source.document_id, source.chunk_id, source.source_type),
                )
