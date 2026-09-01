from __future__ import annotations

from datetime import datetime, timedelta

from app.database.sqlite import get_connection

import logging

logger = logging.getLogger(__name__)


def get_activity_summary(days: int = 7) -> dict:
    """Get activity summary for the last N days."""
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

    summary = {
        "files_changed": 0,
        "commits": 0,
        "bugs_solved": 0,
        "bugs_created": 0,
        "decisions_made": 0,
        "memories_created": 0,
        "tasks_created": 0,
        "tasks_completed": 0,
    }

    with get_connection() as conn:
        # Files changed
        try:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM documents WHERE modified_at > ?",
                (cutoff,)
            ).fetchone()
            summary["files_changed"] = row["cnt"]
        except Exception:
            pass

        # Commits
        try:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM project_commits WHERE committed_at > ?",
                (cutoff,)
            ).fetchone()
            summary["commits"] = row["cnt"]
        except Exception:
            pass

        # Bugs
        try:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM bugs WHERE resolved_at > ?",
                (cutoff,)
            ).fetchone()
            summary["bugs_solved"] = row["cnt"]

            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM bugs WHERE created_at > ?",
                (cutoff,)
            ).fetchone()
            summary["bugs_created"] = row["cnt"]
        except Exception:
            pass

        # Decisions
        try:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM decisions WHERE created_at > ?",
                (cutoff,)
            ).fetchone()
            summary["decisions_made"] = row["cnt"]
        except Exception:
            pass

        # Memories
        try:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM memory_events WHERE created_at > ?",
                (cutoff,)
            ).fetchone()
            summary["memories_created"] = row["cnt"]
        except Exception:
            pass

        # Tasks
        try:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM tasks WHERE created_at > ?",
                (cutoff,)
            ).fetchone()
            summary["tasks_created"] = row["cnt"]

            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM tasks WHERE status = 'completed'"
            ).fetchone()
            summary["tasks_completed"] = row["cnt"]
        except Exception:
            pass

    return summary


def get_recent_activity(limit: int = 20) -> list[dict]:
    """Get recent activity across all sources."""
    activities = []

    with get_connection() as conn:
        # Recent commits
        try:
            rows = conn.execute(
                """SELECT commit_hash, message, author, committed_at as timestamp,
                          'commit' as type
                   FROM project_commits
                   ORDER BY committed_at DESC LIMIT ?""",
                (limit,)
            ).fetchall()
            for r in rows:
                activities.append({
                    "type": "commit",
                    "title": r["message"][:60],
                    "detail": r["commit_hash"][:8],
                    "timestamp": r["timestamp"],
                })
        except Exception:
            pass

        # Recent bugs
        try:
            rows = conn.execute(
                """SELECT id, title, created_at as timestamp, 'bug' as type
                   FROM bugs
                   ORDER BY created_at DESC LIMIT ?""",
                (limit,)
            ).fetchall()
            for r in rows:
                activities.append({
                    "type": "bug",
                    "title": r["title"][:60],
                    "detail": r["id"],
                    "timestamp": r["timestamp"],
                })
        except Exception:
            pass

        # Recent decisions
        try:
            rows = conn.execute(
                """SELECT id, title, date as timestamp, 'decision' as type
                   FROM decisions
                   ORDER BY created_at DESC LIMIT ?""",
                (limit,)
            ).fetchall()
            for r in rows:
                activities.append({
                    "type": "decision",
                    "title": r["title"][:60],
                    "detail": r["date"],
                    "timestamp": r["timestamp"],
                })
        except Exception:
            pass

        # Recent memory events
        try:
            rows = conn.execute(
                """SELECT id, title, type, timestamp
                   FROM memory_events
                   ORDER BY created_at DESC LIMIT ?""",
                (limit,)
            ).fetchall()
            for r in rows:
                activities.append({
                    "type": "memory",
                    "title": r["title"][:60],
                    "detail": r["type"],
                    "timestamp": r["timestamp"],
                })
        except Exception:
            pass

    # Sort by timestamp
    activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return activities[:limit]


def get_last_session() -> dict | None:
    """Get the last session info."""
    with get_connection() as conn:
        # Last commit
        try:
            row = conn.execute(
                """SELECT commit_hash, message, committed_at
                   FROM project_commits
                   ORDER BY committed_at DESC LIMIT 1"""
            ).fetchone()
            if row:
                return {
                    "type": "commit",
                    "hash": row["commit_hash"][:8],
                    "message": row["message"],
                    "timestamp": row["committed_at"],
                }
        except Exception:
            pass

        # Last bug
        try:
            row = conn.execute(
                """SELECT id, title, created_at
                   FROM bugs
                   ORDER BY created_at DESC LIMIT 1"""
            ).fetchone()
            if row:
                return {
                    "type": "bug",
                    "id": row["id"],
                    "title": row["title"],
                    "timestamp": row["created_at"],
                }
        except Exception:
            pass

    return None


def get_project_stats() -> list[dict]:
    """Get stats per project."""
    with get_connection() as conn:
        try:
            rows = conn.execute(
                """SELECT p.id, p.name,
                          (SELECT COUNT(*) FROM project_files WHERE project_id = p.id) as file_count,
                          (SELECT COUNT(*) FROM project_commits WHERE project_id = p.id) as commit_count,
                          (SELECT COUNT(*) FROM bugs WHERE project_id = p.id) as bug_count,
                          (SELECT COUNT(*) FROM decisions WHERE project_id = p.id) as decision_count
                   FROM projects p
                   WHERE p.status = 'active'
                   ORDER BY commit_count DESC"""
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []


def generate_daily_briefing() -> str:
    """Generate a daily briefing summary."""
    today = get_activity_summary(days=1)
    week = get_activity_summary(days=7)
    last_session = get_last_session()
    open_tasks = _get_open_tasks_count()

    lines = []
    lines.append("=== Daily Briefing ===\n")

    # Today
    lines.append("Bugun:")
    if today["files_changed"]:
        lines.append(f"  - {today['files_changed']} dosya degisti")
    if today["commits"]:
        lines.append(f"  - {today['commits']} commit yaptin")
    if today["bugs_solved"]:
        lines.append(f"  - {today['bugs_solved']} bug cozdun")
    if today["decisions_made"]:
        lines.append(f"  - {today['decisions_made']} karar verdin")

    if not any(today.values()):
        lines.append("  - Henuz aktivite yok")

    # This week
    lines.append("\nBu hafta:")
    lines.append(f"  - {week['files_changed']} dosya degisti")
    lines.append(f"  - {week['commits']} commit")
    lines.append(f"  - {week['bugs_solved']} bug cozuldu")
    lines.append(f"  - {week['decisions_made']} karar")
    lines.append(f"  - {week['memories_created']} memory olusturuldu")

    # Last session
    if last_session:
        lines.append("\nSon aktivite:")
        if last_session["type"] == "commit":
            lines.append(f"  - Commit: {last_session['message'][:50]}")
        elif last_session["type"] == "bug":
            lines.append(f"  - Bug: {last_session['title'][:50]}")

    # Open tasks
    if open_tasks > 0:
        lines.append(f"\nAcik gorevler: {open_tasks}")

    return "\n".join(lines)


def _get_open_tasks_count() -> int:
    """Get count of open tasks."""
    with get_connection() as conn:
        try:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM tasks WHERE status = 'open'"
            ).fetchone()
            return row["cnt"]
        except Exception:
            return 0
