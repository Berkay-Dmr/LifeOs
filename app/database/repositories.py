from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from app.database.sqlite import get_connection
from app.models.document import Document
from app.models.chunk import Chunk
from app.models.memory import Memory
from app.models.chat import ChatSession, ChatMessage


# ── Documents ──────────────────────────────────────────────

def insert_document(doc: Document) -> None:
    with get_connection() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO documents
               (id, path, name, extension, mime_type, size, content_hash,
                created_at, modified_at, indexed_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                doc.id, doc.path, doc.name, doc.extension, doc.mime_type,
                doc.size, doc.content_hash, doc.created_at.isoformat(),
                doc.modified_at.isoformat(), doc.indexed_at.isoformat(),
                doc.status,
            ),
        )


def get_document_by_path(path: str) -> Optional[Document]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE path = ?", (path,)
        ).fetchone()
        if row is None:
            return None
        return Document(
            id=row["id"], path=row["path"], name=row["name"],
            extension=row["extension"], mime_type=row["mime_type"],
            size=row["size"], content_hash=row["content_hash"],
            created_at=datetime.fromisoformat(row["created_at"]),
            modified_at=datetime.fromisoformat(row["modified_at"]),
            indexed_at=datetime.fromisoformat(row["indexed_at"]),
            status=row["status"],
        )


def get_document_by_id(doc_id: str) -> Optional[Document]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE id = ?", (doc_id,)
        ).fetchone()
        if row is None:
            return None
        return Document(
            id=row["id"], path=row["path"], name=row["name"],
            extension=row["extension"], mime_type=row["mime_type"],
            size=row["size"], content_hash=row["content_hash"],
            created_at=datetime.fromisoformat(row["created_at"]),
            modified_at=datetime.fromisoformat(row["modified_at"]),
            indexed_at=datetime.fromisoformat(row["indexed_at"]),
            status=row["status"],
        )


def update_document_status(doc_id: str, status: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE documents SET status = ? WHERE id = ?", (status, doc_id)
        )


def delete_document(doc_id: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))


def list_documents() -> list[Document]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM documents ORDER BY modified_at DESC").fetchall()
        return [
            Document(
                id=r["id"], path=r["path"], name=r["name"],
                extension=r["extension"], mime_type=r["mime_type"],
                size=r["size"], content_hash=r["content_hash"],
                created_at=datetime.fromisoformat(r["created_at"]),
                modified_at=datetime.fromisoformat(r["modified_at"]),
                indexed_at=datetime.fromisoformat(r["indexed_at"]),
                status=r["status"],
            )
            for r in rows
        ]


def count_documents() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]


def document_exists(path: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM documents WHERE path = ?", (path,)
        ).fetchone()
        return row is not None


def get_document_hash(path: str) -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT content_hash FROM documents WHERE path = ?", (path,)
        ).fetchone()
        return row["content_hash"] if row else None


# ── Chunks ─────────────────────────────────────────────────

def insert_chunk(chunk: Chunk) -> None:
    with get_connection() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO chunks
               (id, document_id, text, start_offset, end_offset,
                page, section, embedding_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                chunk.id, chunk.document_id, chunk.text,
                chunk.start_offset, chunk.end_offset,
                chunk.page, chunk.section, chunk.embedding_id,
                chunk.created_at.isoformat(),
            ),
        )


def delete_chunks_for_document(doc_id: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))


def count_chunks() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]


def get_chunks_for_document(doc_id: str) -> list[Chunk]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM chunks WHERE document_id = ? ORDER BY start_offset",
            (doc_id,),
        ).fetchall()
        return [
            Chunk(
                id=r["id"], document_id=r["document_id"], text=r["text"],
                start_offset=r["start_offset"], end_offset=r["end_offset"],
                page=r["page"], section=r["section"],
                embedding_id=r["embedding_id"],
                created_at=datetime.fromisoformat(r["created_at"]),
            )
            for r in rows
        ]


def get_all_chunks() -> list[Chunk]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM chunks ORDER BY id").fetchall()
        return [
            Chunk(
                id=r["id"], document_id=r["document_id"], text=r["text"],
                start_offset=r["start_offset"], end_offset=r["end_offset"],
                page=r["page"], section=r["section"],
                embedding_id=r["embedding_id"],
                created_at=datetime.fromisoformat(r["created_at"]),
            )
            for r in rows
        ]


# ── Memories ───────────────────────────────────────────────

def insert_memory(memory: Memory) -> None:
    with get_connection() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO memories
               (id, type, content, confidence, source_count, active,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                memory.id, memory.type, memory.content,
                memory.confidence, memory.source_count,
                int(memory.active), memory.created_at.isoformat(),
                memory.updated_at.isoformat(),
            ),
        )


def delete_memory(memory_id: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE memories SET active = 0 WHERE id = ?", (memory_id,)
        )


def list_memories(active_only: bool = True) -> list[Memory]:
    with get_connection() as conn:
        q = "SELECT * FROM memories"
        if active_only:
            q += " WHERE active = 1"
        q += " ORDER BY created_at DESC"
        rows = conn.execute(q).fetchall()
        return [
            Memory(
                id=r["id"], type=r["type"], content=r["content"],
                confidence=r["confidence"], source_count=r["source_count"],
                active=bool(r["active"]),
                created_at=datetime.fromisoformat(r["created_at"]),
                updated_at=datetime.fromisoformat(r["updated_at"]),
            )
            for r in rows
        ]


def count_memories() -> int:
    with get_connection() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM memories WHERE active = 1"
        ).fetchone()[0]


# ── Chat ───────────────────────────────────────────────────

def create_chat_session(title: str) -> ChatSession:
    session_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chat_sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (session_id, title, now, now),
        )
    return ChatSession(id=session_id, title=title)


def add_chat_message(session_id: str, role: str, content: str) -> ChatMessage:
    msg_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chat_messages (id, session_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (msg_id, session_id, role, content, now),
        )
        conn.execute(
            "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
            (now, session_id),
        )
    return ChatMessage(id=msg_id, session_id=session_id, role=role, content=content)


def get_chat_history(session_id: str, limit: int = 20) -> list[ChatMessage]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM chat_messages
               WHERE session_id = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (session_id, limit),
        ).fetchall()
        return [
            ChatMessage(
                id=r["id"], session_id=r["session_id"],
                role=r["role"], content=r["content"],
                created_at=datetime.fromisoformat(r["created_at"]),
            )
            for r in reversed(rows)
        ]


# ── Index Metadata ─────────────────────────────────────────

def set_index_meta(key: str, value: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO index_metadata (key, value) VALUES (?, ?)",
            (key, value),
        )


def get_index_meta(key: str) -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT value FROM index_metadata WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None
