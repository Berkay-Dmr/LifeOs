from __future__ import annotations

import re
import uuid
from datetime import datetime
from dataclasses import dataclass

from app.database.sqlite import get_connection

import logging

logger = logging.getLogger(__name__)

# Common entity patterns
ENTITY_PATTERNS: dict[str, list[re.Pattern]] = {
    "technology": [
        re.compile(r"\b(PostgreSQL|MySQL|Redis|Docker|Kubernetes|Git|Python|JavaScript|TypeScript|C#|Java|React|Node\.js|Linux|Windows|AWS|Azure|GCP)\b", re.IGNORECASE),
    ],
    "error": [
        re.compile(r"\b(connection refused|timeout|permission denied|not found|out of memory|segmentation fault|stack overflow|rate limit|404|500|503)\b", re.IGNORECASE),
    ],
    "concept": [
        re.compile(r"\b(caching|authentication|database|API|REST|GraphQL|microservice|CI/CD|deployment|containerization|indexing|embedding)\b", re.IGNORECASE),
    ],
}


@dataclass
class Entity:
    id: str
    name: str
    type: str
    created_at: datetime


def extract_entities(text: str) -> list[Entity]:
    """Extract entities from text using pattern matching."""
    entities: list[Entity] = []
    seen: set[str] = set()

    for entity_type, patterns in ENTITY_PATTERNS.items():
        for pattern in patterns:
            for match in pattern.finditer(text):
                name = match.group(0).strip()
                key = f"{name.lower()}:{entity_type}"
                if key not in seen:
                    seen.add(key)
                    entities.append(Entity(
                        id=str(uuid.uuid4())[:12],
                        name=name,
                        type=entity_type,
                        created_at=datetime.utcnow(),
                    ))

    return entities


def store_entity(entity: Entity) -> None:
    """Store an entity in the database."""
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO entities (id, name, type, created_at) VALUES (?, ?, ?, ?)",
            (entity.id, entity.name, entity.type, entity.created_at.isoformat()),
        )


def list_entities(entity_type: str | None = None) -> list[Entity]:
    """List all entities, optionally filtered by type."""
    with get_connection() as conn:
        if entity_type:
            rows = conn.execute(
                "SELECT * FROM entities WHERE type = ? ORDER BY name",
                (entity_type,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM entities ORDER BY type, name"
            ).fetchall()

        return [
            Entity(
                id=r["id"],
                name=r["name"],
                type=r["type"],
                created_at=datetime.fromisoformat(r["created_at"]),
            )
            for r in rows
        ]


def count_entities() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
