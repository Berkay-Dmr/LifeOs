from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.database.repositories import list_documents, list_memories

import logging

logger = logging.getLogger(__name__)


@dataclass
class TimelineEvent:
    date: str
    event_type: str  # document | memory
    title: str
    detail: str = ""
    source_path: str | None = None


def build_timeline(days: int = 30) -> list[TimelineEvent]:
    """Build a timeline of recent events from documents and memories."""
    events: list[TimelineEvent] = []

    # Document events
    for doc in list_documents():
        try:
            mod_date = doc.modified_at.strftime("%Y-%m-%d")
        except Exception:
            continue

        events.append(TimelineEvent(
            date=mod_date,
            event_type="document",
            title=f"Updated: {doc.name}",
            detail=f"File modified in {doc.path.rsplit('/', 1)[0] if '/' in doc.path else '.'}",
            source_path=doc.path,
        ))

        if doc.created_at != doc.modified_at:
            try:
                create_date = doc.created_at.strftime("%Y-%m-%d")
            except Exception:
                continue
            events.append(TimelineEvent(
                date=create_date,
                event_type="document",
                title=f"Created: {doc.name}",
                detail=f"New file: {doc.path}",
                source_path=doc.path,
            ))

    # Memory events
    for mem in list_memories(active_only=True):
        try:
            mem_date = mem.created_at.strftime("%Y-%m-%d")
        except Exception:
            continue

        events.append(TimelineEvent(
            date=mem_date,
            event_type="memory",
            title=f"[{mem.type}] {mem.content[:60]}",
            detail=f"Memory created (confidence: {mem.confidence:.0%})",
        ))

    events.sort(key=lambda e: e.date, reverse=True)

    if days > 0:
        cutoff = datetime.utcnow().strftime("%Y-%m-%d")
        events = [e for e in events if e.date <= cutoff]

    return events[:50]


def build_project_timeline(project_path: str) -> list[TimelineEvent]:
    """Build timeline for a specific project/directory."""
    events: list[TimelineEvent] = []

    for doc in list_documents():
        if doc.path.startswith(project_path):
            try:
                mod_date = doc.modified_at.strftime("%Y-%m-%d")
            except Exception:
                continue

            events.append(TimelineEvent(
                date=mod_date,
                event_type="document",
                title=doc.name,
                detail=doc.path,
                source_path=doc.path,
            ))

    events.sort(key=lambda e: e.date, reverse=True)
    return events[:30]
