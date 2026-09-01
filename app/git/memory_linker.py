from __future__ import annotations

import uuid
from datetime import datetime

from app.database.sqlite import get_connection

import logging

logger = logging.getLogger(__name__)


def link_commit_to_memory(
    commit_hash: str,
    memory_event_id: str | None = None,
    decision_id: str | None = None,
    bug_id: str | None = None,
    link_type: str = "relates_to",
) -> None:
    """Link a git commit to a memory event, decision, or bug."""
    link_id = str(uuid.uuid4())[:12]
    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        conn.execute(
            """INSERT INTO git_memory_links
               (id, commit_hash, memory_event_id, decision_id, bug_id, link_type, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (link_id, commit_hash, memory_event_id, decision_id, bug_id, link_type, now),
        )

    logger.info("Linked commit %s to memory (%s)", commit_hash[:8], link_type)


def get_commit_links(commit_hash: str) -> list[dict]:
    """Get all memory links for a commit."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT gml.*,
                      me.title as memory_title, me.type as memory_type,
                      d.title as decision_title, d.status as decision_status,
                      b.title as bug_title, b.resolved as bug_resolved
               FROM git_memory_links gml
               LEFT JOIN memory_events me ON gml.memory_event_id = me.id
               LEFT JOIN decisions d ON gml.decision_id = d.id
               LEFT JOIN bugs b ON gml.bug_id = b.id
               WHERE gml.commit_hash = ?""",
            (commit_hash,)
        ).fetchall()

        results = []
        for r in rows:
            results.append({
                "link_id": r["id"],
                "commit_hash": r["commit_hash"],
                "link_type": r["link_type"],
                "memory": {
                    "id": r["memory_event_id"],
                    "title": r["memory_title"],
                    "type": r["memory_type"],
                } if r["memory_event_id"] else None,
                "decision": {
                    "id": r["decision_id"],
                    "title": r["decision_title"],
                    "status": r["decision_status"],
                } if r["decision_id"] else None,
                "bug": {
                    "id": r["bug_id"],
                    "title": r["bug_title"],
                    "resolved": bool(r["bug_resolved"]),
                } if r["bug_id"] else None,
            })

        return results


def get_memory_commits(memory_event_id: str) -> list[dict]:
    """Get all commits linked to a memory event."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT gml.*, c.message, c.author, c.committed_at
               FROM git_memory_links gml
               LEFT JOIN project_commits c ON gml.commit_hash = c.commit_hash
               WHERE gml.memory_event_id = ?""",
            (memory_event_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_decision_commits(decision_id: str) -> list[dict]:
    """Get all commits linked to a decision."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT gml.*, c.message, c.author, c.committed_at
               FROM git_memory_links gml
               LEFT JOIN project_commits c ON gml.commit_hash = c.commit_hash
               WHERE gml.decision_id = ?""",
            (decision_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_bug_commits(bug_id: str) -> list[dict]:
    """Get all commits linked to a bug."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT gml.*, c.message, c.author, c.committed_at
               FROM git_memory_links gml
               LEFT JOIN project_commits c ON gml.commit_hash = c.commit_hash
               WHERE gml.bug_id = ?""",
            (bug_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def auto_link_commit(commit_hash: str, commit_message: str) -> list[str]:
    """Auto-link a commit based on its message content."""
    linked = []
    msg_lower = commit_message.lower()

    # Check for bug fix patterns
    bug_keywords = ["fix", "bug", "error", "issue", "resolve", "patch"]
    if any(kw in msg_lower for kw in bug_keywords):
        # Find recent unresolved bugs
        with get_connection() as conn:
            bugs = conn.execute(
                """SELECT id, title FROM bugs
                   WHERE resolved = 0
                   ORDER BY first_seen DESC LIMIT 5"""
            ).fetchall()

            for bug in bugs:
                if any(word in bug["title"].lower() for word in msg_lower.split()):
                    link_commit_to_memory(commit_hash, bug_id=bug["id"], link_type="fixes")
                    linked.append(f"bug:{bug['title']}")
                    # Auto-resolve the bug
                    conn.execute(
                        "UPDATE bugs SET resolved = 1, solution = ? WHERE id = ?",
                        (commit_message, bug["id"])
                    )
                    break

    # Check for decision patterns
    decision_keywords = ["decide", "decision", "choose", "switch", "replace", "migrate"]
    if any(kw in msg_lower for kw in decision_keywords):
        with get_connection() as conn:
            decisions = conn.execute(
                """SELECT id, title FROM decisions
                   WHERE status = 'active'
                   ORDER BY date DESC LIMIT 5"""
            ).fetchall()

            for dec in decisions:
                if any(word in dec["title"].lower() for word in msg_lower.split()):
                    link_commit_to_memory(commit_hash, decision_id=dec["id"], link_type="implements")
                    linked.append(f"decision:{dec['title']}")
                    break

    return linked


def search_git_links(query: str) -> list[dict]:
    """Search git-memory links."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT gml.*,
                      me.title as memory_title,
                      d.title as decision_title,
                      b.title as bug_title
               FROM git_memory_links gml
               LEFT JOIN memory_events me ON gml.memory_event_id = me.id
               LEFT JOIN decisions d ON gml.decision_id = d.id
               LEFT JOIN bugs b ON gml.bug_id = b.id
               WHERE me.title LIKE ? OR d.title LIKE ? OR b.title LIKE ?
               ORDER BY gml.created_at DESC LIMIT 20""",
            (f"%{query}%", f"%{query}%", f"%{query}%")
        ).fetchall()
        return [dict(r) for r in rows]
