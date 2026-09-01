from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Project:
    id: str
    name: str
    path: str
    language: str | None = None
    framework: str | None = None
    description: str | None = None
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_row(cls, row) -> Project:
        return cls(
            id=row["id"],
            name=row["name"],
            path=row["path"],
            language=row["language"],
            framework=row["framework"],
            description=row["description"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


@dataclass
class MemoryEvent:
    id: str
    timestamp: str
    type: str
    title: str
    project_id: str | None = None
    description: str | None = None
    entities: list[str] = field(default_factory=list)
    source: str | None = None
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_row(cls, row) -> MemoryEvent:
        import json
        entities = []
        if row["entities"]:
            try:
                entities = json.loads(row["entities"])
            except Exception:
                pass
        return cls(
            id=row["id"],
            timestamp=row["timestamp"],
            type=row["type"],
            title=row["title"],
            project_id=row["project_id"],
            description=row["description"],
            entities=entities,
            source=row["source"],
            confidence=row["confidence"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )


@dataclass
class Decision:
    id: str
    title: str
    date: str
    status: str = "active"
    project_id: str | None = None
    reason: str | None = None
    alternatives: list[str] = field(default_factory=list)
    superseded_by: str | None = None
    confidence: float = 1.0
    source: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_row(cls, row) -> Decision:
        import json
        alternatives = []
        if row["alternatives"]:
            try:
                alternatives = json.loads(row["alternatives"])
            except Exception:
                pass
        return cls(
            id=row["id"],
            title=row["title"],
            date=row["date"],
            status=row["status"],
            project_id=row["project_id"],
            reason=row["reason"],
            alternatives=alternatives,
            superseded_by=row["superseded_by"],
            confidence=row["confidence"],
            source=row["source"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )


@dataclass
class Bug:
    id: str
    title: str
    first_seen: str
    resolved: bool = False
    error_message: str | None = None
    project_id: str | None = None
    cause: str | None = None
    solution: str | None = None
    resolved_at: str | None = None
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_row(cls, row) -> Bug:
        return cls(
            id=row["id"],
            title=row["title"],
            first_seen=row["first_seen"],
            resolved=bool(row["resolved"]),
            error_message=row["error_message"],
            project_id=row["project_id"],
            cause=row["cause"],
            solution=row["solution"],
            resolved_at=row["resolved_at"],
            confidence=row["confidence"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
