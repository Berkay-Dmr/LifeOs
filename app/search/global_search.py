from __future__ import annotations

from dataclasses import dataclass, field

from app.database.sqlite import get_connection

import logging

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Unified search result."""
    type: str  # file, code, commit, bug, decision, memory, task
    title: str
    snippet: str = ""
    source: str = ""
    score: float = 0.0
    metadata: dict = field(default_factory=dict)


def global_search(query: str, limit: int = 50) -> dict[str, list[SearchResult]]:
    """Search across all data sources."""
    results = {
        "files": [],
        "code": [],
        "commits": [],
        "bugs": [],
        "decisions": [],
        "memory": [],
        "tasks": [],
    }

    try:
        results["files"] = _search_files(query, limit)
    except Exception as e:
        logger.debug("File search failed: %s", e)

    try:
        results["code"] = _search_code(query, limit)
    except Exception as e:
        logger.debug("Code search failed: %s", e)

    try:
        results["commits"] = _search_commits(query, limit)
    except Exception as e:
        logger.debug("Commit search failed: %s", e)

    try:
        results["bugs"] = _search_bugs(query, limit)
    except Exception as e:
        logger.debug("Bug search failed: %s", e)

    try:
        results["decisions"] = _search_decisions(query, limit)
    except Exception as e:
        logger.debug("Decision search failed: %s", e)

    try:
        results["memory"] = _search_memory(query, limit)
    except Exception as e:
        logger.debug("Memory search failed: %s", e)

    try:
        results["tasks"] = _search_tasks(query, limit)
    except Exception as e:
        logger.debug("Task search failed: %s", e)

    return results


def _search_files(query: str, limit: int) -> list[SearchResult]:
    """Search files by name and content."""
    results = []

    with get_connection() as conn:
        # Search by name
        rows = conn.execute(
            """SELECT id, name, path, extension
               FROM documents
               WHERE name LIKE ? OR path LIKE ?
               LIMIT ?""",
            (f"%{query}%", f"%{query}%", limit)
        ).fetchall()

        for r in rows:
            results.append(SearchResult(
                type="file",
                title=r["name"],
                snippet=r["path"],
                source=r["path"],
                metadata={"extension": r["extension"], "id": r["id"]},
            ))

    return results


def _search_code(query: str, limit: int) -> list[SearchResult]:
    """Search code dependencies."""
    results = []

    with get_connection() as conn:
        rows = conn.execute(
            """SELECT file_path, calls_function, calls_file, dependency_type
               FROM code_dependencies
               WHERE calls_function LIKE ? OR calls_file LIKE ? OR file_path LIKE ?
               LIMIT ?""",
            (f"%{query}%", f"%{query}%", f"%{query}%", limit)
        ).fetchall()

        for r in rows:
            target = r["calls_function"] or r["calls_file"] or "-"
            results.append(SearchResult(
                type="code",
                title=target,
                snippet=f"{r['dependency_type']} in {r['file_path']}",
                source=r["file_path"],
                metadata={"type": r["dependency_type"]},
            ))

    return results


def _search_commits(query: str, limit: int) -> list[SearchResult]:
    """Search git commits."""
    results = []

    with get_connection() as conn:
        rows = conn.execute(
            """SELECT commit_hash, message, author, committed_at
               FROM project_commits
               WHERE message LIKE ? OR commit_hash LIKE ?
               LIMIT ?""",
            (f"%{query}%", f"%{query}%", limit)
        ).fetchall()

        for r in rows:
            results.append(SearchResult(
                type="commit",
                title=r["commit_hash"][:8],
                snippet=r["message"],
                source=r["commit_hash"],
                metadata={"author": r["author"], "date": r["committed_at"]},
            ))

    return results


def _search_bugs(query: str, limit: int) -> list[SearchResult]:
    """Search bugs."""
    results = []

    with get_connection() as conn:
        rows = conn.execute(
            """SELECT id, title, error_message, cause, solution, resolved
               FROM bugs
               WHERE title LIKE ? OR error_message LIKE ? OR cause LIKE ?
               LIMIT ?""",
            (f"%{query}%", f"%{query}%", f"%{query}%", limit)
        ).fetchall()

        for r in rows:
            status = "resolved" if r["resolved"] else "open"
            results.append(SearchResult(
                type="bug",
                title=r["title"],
                snippet=r["error_message"] or r["cause"] or "",
                source=f"bug:{r['id']}",
                metadata={"status": status, "solution": r["solution"]},
            ))

    return results


def _search_decisions(query: str, limit: int) -> list[SearchResult]:
    """Search decisions."""
    results = []

    with get_connection() as conn:
        rows = conn.execute(
            """SELECT id, title, reason, status, date
               FROM decisions
               WHERE title LIKE ? OR reason LIKE ?
               LIMIT ?""",
            (f"%{query}%", f"%{query}%", limit)
        ).fetchall()

        for r in rows:
            results.append(SearchResult(
                type="decision",
                title=r["title"],
                snippet=r["reason"] or "",
                source=f"decision:{r['id']}",
                metadata={"status": r["status"], "date": r["date"]},
            ))

    return results


def _search_memory(query: str, limit: int) -> list[SearchResult]:
    """Search memory events."""
    results = []

    with get_connection() as conn:
        rows = conn.execute(
            """SELECT id, title, description, type, timestamp
               FROM memory_events
               WHERE title LIKE ? OR description LIKE ?
               LIMIT ?""",
            (f"%{query}%", f"%{query}%", limit)
        ).fetchall()

        for r in rows:
            results.append(SearchResult(
                type="memory",
                title=r["title"],
                snippet=r["description"] or "",
                source=f"memory:{r['id']}",
                metadata={"type": r["type"], "timestamp": r["timestamp"]},
            ))

    return results


def _search_tasks(query: str, limit: int) -> list[SearchResult]:
    """Search tasks/TODOs."""
    results = []

    with get_connection() as conn:
        rows = conn.execute(
            """SELECT id, text, priority, status, source
               FROM tasks
               WHERE text LIKE ? AND status = 'open'
               LIMIT ?""",
            (f"%{query}%", limit)
        ).fetchall()

        for r in rows:
            results.append(SearchResult(
                type="task",
                title=r["text"][:60],
                snippet=f"Priority: {r['priority']}",
                source=r["source"] or "",
                metadata={"priority": r["priority"], "status": r["status"]},
            ))

    return results


def get_search_stats() -> dict:
    """Get statistics about searchable content."""
    stats = {}

    with get_connection() as conn:
        stats["files"] = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        stats["chunks"] = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]

        try:
            stats["code_deps"] = conn.execute("SELECT COUNT(*) FROM code_dependencies").fetchone()[0]
        except Exception:
            stats["code_deps"] = 0

        try:
            stats["commits"] = conn.execute("SELECT COUNT(*) FROM project_commits").fetchone()[0]
        except Exception:
            stats["commits"] = 0

        try:
            stats["bugs"] = conn.execute("SELECT COUNT(*) FROM bugs").fetchone()[0]
        except Exception:
            stats["bugs"] = 0

        try:
            stats["decisions"] = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
        except Exception:
            stats["decisions"] = 0

        try:
            stats["memory_events"] = conn.execute("SELECT COUNT(*) FROM memory_events").fetchone()[0]
        except Exception:
            stats["memory_events"] = 0

        try:
            stats["tasks"] = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'open'").fetchone()[0]
        except Exception:
            stats["tasks"] = 0

    return stats
