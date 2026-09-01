from __future__ import annotations

import re
import uuid
from datetime import datetime

from app.database.sqlite import get_connection

import logging

logger = logging.getLogger(__name__)


# ── Memory Deduplication ─────────────────────────────────────────────────────

def check_duplicate(content: str, memory_type: str = "fact") -> dict | None:
    """Check if a similar memory already exists."""
    content_lower = content.lower().strip()

    with get_connection() as conn:
        # Get existing memories of same type
        rows = conn.execute(
            """SELECT id, type, content, confidence, source_count
               FROM memories
               WHERE type = ? AND active = 1
               ORDER BY created_at DESC LIMIT 50""",
            (memory_type,)
        ).fetchall()

        for row in rows:
            existing = row["content"].lower().strip()
            similarity = _calculate_similarity(content_lower, existing)

            if similarity > 0.8:
                return {
                    "existing_id": row["id"],
                    "existing_content": row["content"],
                    "similarity": similarity,
                    "merge_suggestion": True,
                    "source_count": row["source_count"],
                }

    return None


def _calculate_similarity(a: str, b: str) -> float:
    """Simple word-based similarity calculation."""
    words_a = set(a.split())
    words_b = set(b.split())

    if not words_a or not words_b:
        return 0.0

    intersection = words_a & words_b
    union = words_a | words_b

    return len(intersection) / len(union)


def merge_memories(existing_id: str, new_content: str) -> None:
    """Merge new content into existing memory."""
    with get_connection() as conn:
        # Get existing memory
        row = conn.execute(
            "SELECT content, source_count FROM memories WHERE id = ?",
            (existing_id,)
        ).fetchone()

        if row:
            new_count = row["source_count"] + 1
            conn.execute(
                """UPDATE memories
                   SET source_count = ?, updated_at = ?
                   WHERE id = ?""",
                (new_count, datetime.utcnow().isoformat(), existing_id)
            )
            logger.info("Merged memory %s (count: %d)", existing_id, new_count)


# ── Contradiction Detection ──────────────────────────────────────────────────

def detect_contradiction(title: str, project_id: str | None = None) -> list[dict]:
    """Detect if a new decision contradicts existing ones."""
    contradictions = []

    with get_connection() as conn:
        # Get active decisions
        if project_id:
            rows = conn.execute(
                """SELECT id, title, reason, alternatives, date
                   FROM decisions
                   WHERE status = 'active' AND project_id = ?
                   ORDER BY date DESC LIMIT 20""",
                (project_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT id, title, reason, alternatives, date
                   FROM decisions
                   WHERE status = 'active'
                   ORDER BY date DESC LIMIT 20"""
            ).fetchall()

        title_lower = title.lower()
        words_new = set(title_lower.split())

        for row in rows:
            existing_title = row["title"].lower()
            words_existing = set(existing_title.split())

            # Check for opposite patterns
            opposite_pairs = [
                ("use", "don't use"),
                ("enable", "disable"),
                ("add", "remove"),
                ("switch", "stay"),
                ("migrate", "keep"),
                ("upgrade", "downgrade"),
                ("yes", "no"),
            ]

            for pos, neg in opposite_pairs:
                if (pos in words_new and neg in words_existing) or \
                   (neg in words_new and pos in words_existing):
                    contradictions.append({
                        "existing_id": row["id"],
                        "existing_title": row["title"],
                        "existing_date": row["date"],
                        "new_title": title,
                        "type": "opposite",
                        "confidence": 0.8,
                    })

            # Check for similar but different decisions
            similarity = _calculate_similarity(title_lower, existing_title)
            if 0.5 < similarity < 0.9:
                contradictions.append({
                    "existing_id": row["id"],
                    "existing_title": row["title"],
                    "existing_date": row["date"],
                    "new_title": title,
                    "type": "similar_but_different",
                    "confidence": similarity,
                })

    return contradictions


def supersede_decision(decision_id: str, new_title: str, reason: str | None = None) -> str:
    """Mark old decision as superseded and create new one."""
    from app.projects.manager import create_decision

    # Get old decision
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM decisions WHERE id = ?",
            (decision_id,)
        ).fetchone()

    if not row:
        return ""

    # Mark old as superseded
    with get_connection() as conn:
        conn.execute(
            "UPDATE decisions SET status = 'superseded' WHERE id = ?",
            (decision_id,)
        )

    # Create new decision
    new_dec = create_decision(
        title=new_title,
        reason=reason,
        alternatives=row["alternatives"].split(",") if row["alternatives"] else [],
        project_id=row["project_id"],
        source=f"supersedes:{decision_id}",
    )

    # Link old to new
    with get_connection() as conn:
        conn.execute(
            "UPDATE decisions SET superseded_by = ? WHERE id = ?",
            (new_dec.id, decision_id)
        )

    return new_dec.id


# ── TODO/Task Extraction ─────────────────────────────────────────────────────

TODO_PATTERNS = [
    # English
    r"TODO[:\s]+(.+)",
    r"FIXME[:\s]+(.+)",
    r"HACK[:\s]+(.+)",
    r"XXX[:\s]+(.+)",
    r"NOTE[:\s]+(.+)",
    # Turkish
    r"yapm[ae]m?\s+laz[ıi]m[:\s]*(.+)",
    r"düzeltm[ae]m?\s+laz[ıi]m[:\s]*(.+)",
    r"eklem[ae]m?\s+laz[ıi]m[:\s]*(.+)",
    r"değiştir[me]m?\s+laz[ıi]m[:\s]*(.+)",
    r"kaldır[ae]m?\s+laz[ıi]m[:\s]*(.+)",
]

TASK_KEYWORDS = {
    "high": ["critical", "urgent", "important", "acil", "önemli"],
    "medium": ["should", "need", "gerekli", "gereken"],
    "low": ["nice to have", "optional", "isteğe bağlı", "olsa iyi"],
}


def extract_todos_from_text(text: str, source: str | None = None) -> list[dict]:
    """Extract TODO items from text content."""
    todos = []
    lines = text.split("\n")

    for line_num, line in enumerate(lines, 1):
        line_stripped = line.strip()

        for pattern in TODO_PATTERNS:
            match = re.search(pattern, line_stripped, re.IGNORECASE)
            if match:
                task_text = match.group(1).strip()
                if len(task_text) > 5:  # Skip very short matches
                    priority = _detect_priority(task_text)
                    todos.append({
                        "text": task_text,
                        "line": line_num,
                        "source": source,
                        "priority": priority,
                        "status": "open",
                    })

    return todos


def _detect_priority(text: str) -> str:
    """Detect task priority from text."""
    text_lower = text.lower()

    for priority, keywords in TASK_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return priority

    return "medium"


def extract_todos_from_file(file_path: str) -> list[dict]:
    """Extract TODOs from a file."""
    try:
        path = __import__("pathlib").Path(file_path)
        if not path.exists():
            return []

        content = path.read_text(encoding="utf-8", errors="ignore")
        return extract_todos_from_text(content, source=file_path)

    except Exception as e:
        logger.error("Failed to extract TODOs from %s: %s", file_path, e)
        return []


def extract_todos_from_directory(root_path: str) -> list[dict]:
    """Extract TODOs from all code files in a directory."""
    from pathlib import Path

    root = Path(root_path)
    all_todos = []

    code_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".md", ".txt"}

    for file in root.rglob("*"):
        if file.suffix.lower() in code_extensions:
            todos = extract_todos_from_file(str(file))
            all_todos.extend(todos)

    return all_todos


def store_todos(todos: list[dict]) -> int:
    """Store extracted TODOs in database."""
    stored = 0

    with get_connection() as conn:
        # Create table if not exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'open',
                source TEXT,
                line INTEGER,
                project_id TEXT,
                created_at TEXT NOT NULL
            )
        """)

        for todo in todos:
            # Check if already exists
            existing = conn.execute(
                "SELECT id FROM tasks WHERE text = ? AND source = ?",
                (todo["text"], todo.get("source"))
            ).fetchone()

            if not existing:
                task_id = str(uuid.uuid4())[:12]
                now = datetime.utcnow().isoformat()
                conn.execute(
                    """INSERT INTO tasks (id, text, priority, status, source, line, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (task_id, todo["text"], todo["priority"], "open",
                     todo.get("source"), todo.get("line"), now)
                )
                stored += 1

    return stored


def get_open_tasks(project_id: str | None = None) -> list[dict]:
    """Get all open tasks."""
    with get_connection() as conn:
        if project_id:
            rows = conn.execute(
                """SELECT * FROM tasks
                   WHERE status = 'open' AND project_id = ?
                   ORDER BY priority, created_at DESC""",
                (project_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM tasks
                   WHERE status = 'open'
                   ORDER BY
                     CASE priority
                       WHEN 'high' THEN 1
                       WHEN 'medium' THEN 2
                       WHEN 'low' THEN 3
                     END,
                     created_at DESC"""
            ).fetchall()

        return [dict(r) for r in rows]


def complete_task(task_id: str) -> None:
    """Mark a task as completed."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE tasks SET status = 'completed' WHERE id = ?",
            (task_id,)
        )
