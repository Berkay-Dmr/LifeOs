from __future__ import annotations

import uuid
from datetime import datetime
from dataclasses import dataclass

from app.database.sqlite import get_connection

import logging

logger = logging.getLogger(__name__)


@dataclass
class Relation:
    id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: str  # uses, contains, solves, related_to
    created_at: datetime


def create_relation(
    source_id: str,
    target_id: str,
    relation_type: str = "related_to",
) -> Relation:
    """Create a relation between two entities."""
    relation = Relation(
        id=str(uuid.uuid4())[:12],
        source_entity_id=source_id,
        target_entity_id=target_id,
        relation_type=relation_type,
        created_at=datetime.utcnow(),
    )

    with get_connection() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO relations
               (id, source_entity_id, target_entity_id, relation_type, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (relation.id, relation.source_entity_id, relation.target_entity_id,
             relation.relation_type, relation.created_at.isoformat()),
        )

    return relation


def get_relations_for_entity(entity_id: str) -> list[Relation]:
    """Get all relations involving an entity."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM relations
               WHERE source_entity_id = ? OR target_entity_id = ?
               ORDER BY created_at DESC""",
            (entity_id, entity_id),
        ).fetchall()

        return [
            Relation(
                id=r["id"],
                source_entity_id=r["source_entity_id"],
                target_entity_id=r["target_entity_id"],
                relation_type=r["relation_type"],
                created_at=datetime.fromisoformat(r["created_at"]),
            )
            for r in rows
        ]


def count_relations() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
