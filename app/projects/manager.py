from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from app.database.sqlite import get_connection
from app.models.project import Project, MemoryEvent, Decision, Bug

import logging

logger = logging.getLogger(__name__)


# ── Project Operations ───────────────────────────────────────────────────────

def create_project(
    name: str,
    path: str,
    language: str | None = None,
    framework: str | None = None,
    description: str | None = None,
) -> Project:
    """Create a new project."""
    project_id = str(uuid.uuid4())[:12]
    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        conn.execute(
            """INSERT INTO projects (id, name, path, language, framework, description, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)""",
            (project_id, name, path, language, framework, description, now, now),
        )

    logger.info("Created project: %s (%s)", name, project_id)
    return Project(
        id=project_id, name=name, path=path,
        language=language, framework=framework, description=description,
        created_at=datetime.fromisoformat(now),
        updated_at=datetime.fromisoformat(now),
    )


def get_project(project_id: str) -> Project | None:
    """Get project by ID."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if row:
            return Project.from_row(row)
    return None


def get_project_by_path(path: str) -> Project | None:
    """Get project by path."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM projects WHERE path = ?", (path,)).fetchone()
        if row:
            return Project.from_row(row)
    return None


def list_projects(status: str = "active") -> list[Project]:
    """List all projects."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM projects WHERE status = ? ORDER BY updated_at DESC",
            (status,)
        ).fetchall()
        return [Project.from_row(r) for r in rows]


def update_project(project_id: str, **kwargs) -> None:
    """Update project fields."""
    allowed = {"name", "language", "framework", "description", "status"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return

    updates["updated_at"] = datetime.utcnow().isoformat()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [project_id]

    with get_connection() as conn:
        conn.execute(f"UPDATE projects SET {set_clause} WHERE id = ?", values)


def delete_project(project_id: str) -> None:
    """Soft delete a project."""
    update_project(project_id, status="deleted")


def discover_projects(root_path: Path) -> list[Project]:
    """Auto-discover projects in a directory."""
    discovered = []

    for item in root_path.iterdir():
        if not item.is_dir():
            continue

        # Check if it's a project (has git, package.json, requirements.txt, etc.)
        is_project = False
        language = None
        framework = None

        if (item / ".git").exists():
            is_project = True
        if (item / "package.json").exists():
            is_project = True
            framework = "node"
        if (item / "requirements.txt").exists() or (item / "pyproject.toml").exists():
            is_project = True
            language = "python"
        if (item / "Cargo.toml").exists():
            is_project = True
            language = "rust"
        if (item / "go.mod").exists():
            is_project = True
            language = "go"

        if is_project:
            # Check if already exists
            existing = get_project_by_path(str(item))
            if not existing:
                project = create_project(
                    name=item.name,
                    path=str(item),
                    language=language,
                    framework=framework,
                )
                discovered.append(project)
            else:
                discovered.append(existing)

    return discovered


# ── File-Project Linking ─────────────────────────────────────────────────────

def link_file_to_project(project_id: str, document_id: str) -> None:
    """Link a document to a project."""
    link_id = str(uuid.uuid4())[:12]
    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO project_files (id, project_id, document_id, added_at)
               VALUES (?, ?, ?, ?)""",
            (link_id, project_id, document_id, now),
        )


def get_project_files(project_id: str) -> list[str]:
    """Get document IDs for a project."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT document_id FROM project_files WHERE project_id = ?",
            (project_id,)
        ).fetchall()
        return [r["document_id"] for r in rows]


def get_document_projects(document_id: str) -> list[Project]:
    """Get projects that contain a document."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT p.* FROM projects p
               JOIN project_files pf ON p.id = pf.project_id
               WHERE pf.document_id = ?""",
            (document_id,)
        ).fetchall()
        return [Project.from_row(r) for r in rows]


# ── Memory Events ────────────────────────────────────────────────────────────

def create_memory_event(
    title: str,
    event_type: str,
    description: str | None = None,
    project_id: str | None = None,
    entities: list[str] | None = None,
    source: str | None = None,
    confidence: float = 1.0,
) -> MemoryEvent:
    """Create a memory event."""
    import json
    event_id = str(uuid.uuid4())[:12]
    now = datetime.utcnow().isoformat()
    timestamp = now

    with get_connection() as conn:
        conn.execute(
            """INSERT INTO memory_events (id, timestamp, type, project_id, title, description, entities, source, confidence, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (event_id, timestamp, event_type, project_id, title, description,
             json.dumps(entities or []), source, confidence, now),
        )

    return MemoryEvent(
        id=event_id, timestamp=timestamp, type=event_type,
        title=title, project_id=project_id, description=description,
        entities=entities or [], source=source, confidence=confidence,
    )


def search_memory_events(query: str, project_id: str | None = None) -> list[MemoryEvent]:
    """Search memory events."""
    with get_connection() as conn:
        if project_id:
            rows = conn.execute(
                """SELECT * FROM memory_events
                   WHERE project_id = ? AND (title LIKE ? OR description LIKE ?)
                   ORDER BY timestamp DESC LIMIT 20""",
                (project_id, f"%{query}%", f"%{query}%")
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM memory_events
                   WHERE title LIKE ? OR description LIKE ?
                   ORDER BY timestamp DESC LIMIT 20""",
                (f"%{query}%", f"%{query}%")
            ).fetchall()
        return [MemoryEvent.from_row(r) for r in rows]


# ── Decisions ────────────────────────────────────────────────────────────────

def create_decision(
    title: str,
    reason: str | None = None,
    alternatives: list[str] | None = None,
    project_id: str | None = None,
    source: str | None = None,
    confidence: float = 1.0,
) -> Decision:
    """Create a decision."""
    import json
    dec_id = str(uuid.uuid4())[:12]
    now = datetime.utcnow().isoformat()
    date = now[:10]

    with get_connection() as conn:
        conn.execute(
            """INSERT INTO decisions (id, title, date, project_id, reason, alternatives, status, confidence, source, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)""",
            (dec_id, title, date, project_id, reason,
             json.dumps(alternatives or []), confidence, source, now),
        )

    return Decision(
        id=dec_id, title=title, date=date, status="active",
        project_id=project_id, reason=reason,
        alternatives=alternatives or [], confidence=confidence, source=source,
    )


def supersede_decision(decision_id: str, new_title: str, reason: str | None = None) -> Decision:
    """Supersede an existing decision with a new one."""
    # Mark old as superseded
    with get_connection() as conn:
        conn.execute(
            "UPDATE decisions SET status = 'superseded' WHERE id = ?",
            (decision_id,)
        )

    # Create new decision
    return create_decision(
        title=new_title,
        reason=reason,
        source=f"supersedes:{decision_id}",
    )


def search_decisions(query: str, project_id: str | None = None) -> list[Decision]:
    """Search decisions."""
    with get_connection() as conn:
        if project_id:
            rows = conn.execute(
                """SELECT * FROM decisions
                   WHERE project_id = ? AND (title LIKE ? OR reason LIKE ?)
                   ORDER BY date DESC LIMIT 20""",
                (project_id, f"%{query}%", f"%{query}%")
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM decisions
                   WHERE title LIKE ? OR reason LIKE ?
                   ORDER BY date DESC LIMIT 20""",
                (f"%{query}%", f"%{query}%")
            ).fetchall()
        return [Decision.from_row(r) for r in rows]


# ── Bugs ─────────────────────────────────────────────────────────────────────

def create_bug(
    title: str,
    error_message: str | None = None,
    project_id: str | None = None,
    cause: str | None = None,
    solution: str | None = None,
    confidence: float = 1.0,
) -> Bug:
    """Create a bug record."""
    bug_id = str(uuid.uuid4())[:12]
    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        conn.execute(
            """INSERT INTO bugs (id, title, error_message, project_id, cause, solution, resolved, first_seen, confidence, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?)""",
            (bug_id, title, error_message, project_id, cause, solution, now, confidence, now),
        )

    return Bug(
        id=bug_id, title=title, first_seen=now, resolved=False,
        error_message=error_message, project_id=project_id,
        cause=cause, solution=solution, confidence=confidence,
    )


def resolve_bug(bug_id: str, solution: str) -> None:
    """Mark a bug as resolved."""
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        conn.execute(
            "UPDATE bugs SET resolved = 1, solution = ?, resolved_at = ? WHERE id = ?",
            (solution, now, bug_id),
        )


def find_similar_bugs(error_message: str) -> list[Bug]:
    """Find similar bugs by error message."""
    if not error_message:
        return []
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM bugs
               WHERE error_message LIKE ? OR title LIKE ?
               ORDER BY first_seen DESC LIMIT 5""",
            (f"%{error_message[:50]}%", f"%{error_message[:30]}%")
        ).fetchall()
        return [Bug.from_row(r) for r in rows]


def search_bugs(query: str, project_id: str | None = None) -> list[Bug]:
    """Search bugs."""
    with get_connection() as conn:
        if project_id:
            rows = conn.execute(
                """SELECT * FROM bugs
                   WHERE project_id = ? AND (title LIKE ? OR error_message LIKE ? OR cause LIKE ?)
                   ORDER BY first_seen DESC LIMIT 20""",
                (project_id, f"%{query}%", f"%{query}%", f"%{query}%")
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM bugs
                   WHERE title LIKE ? OR error_message LIKE ? OR cause LIKE ?
                   ORDER BY first_seen DESC LIMIT 20""",
                (f"%{query}%", f"%{query}%", f"%{query}%")
            ).fetchall()
        return [Bug.from_row(r) for r in rows]
