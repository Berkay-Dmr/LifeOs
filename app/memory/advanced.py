from __future__ import annotations

import math
from datetime import datetime, timedelta

from app.database.sqlite import get_connection

import logging

logger = logging.getLogger(__name__)


def calculate_importance_score(
    access_count: int,
    created_at: str,
    has_links: bool = False,
    is_decision: bool = False,
    is_bug: bool = False,
) -> float:
    """Calculate importance score for a memory.

    Formula: base_score + recency_bonus + access_bonus + link_bonus + type_bonus
    """
    # Base score
    base = 0.5

    # Recency bonus (exponential decay)
    try:
        created = datetime.fromisoformat(created_at)
        days_old = (datetime.utcnow() - created).days
        recency = math.exp(-days_old / 30)  # 30-day half-life
    except Exception:
        recency = 0.5

    # Access bonus (logarithmic)
    access_bonus = min(0.3, math.log1p(access_count) * 0.1)

    # Link bonus
    link_bonus = 0.15 if has_links else 0

    # Type bonuses
    type_bonus = 0
    if is_decision:
        type_bonus = 0.1
    elif is_bug:
        type_bonus = 0.05

    score = base + recency * 0.3 + access_bonus + link_bonus + type_bonus
    return min(1.0, max(0.0, score))


def apply_temporal_decay(decay_rate: float = 0.01) -> int:
    """Apply temporal decay to all memory scores.

    Returns number of affected records.
    """
    affected = 0

    with get_connection() as conn:
        # Decay memory events
        try:
            conn.execute(
                """UPDATE memory_events
                   SET score = MAX(0.1, score * (1.0 - ?))
                   WHERE score > 0.1""",
                (decay_rate,)
            )
            affected += conn.total_changes
        except Exception:
            pass

        # Decay decisions
        try:
            conn.execute(
                """UPDATE decisions
                   SET score = MAX(0.1, score * (1.0 - ?))
                   WHERE score > 0.1""",
                (decay_rate,)
            )
            affected += conn.total_changes
        except Exception:
            pass

        # Decay bugs
        try:
            conn.execute(
                """UPDATE bugs
                   SET score = MAX(0.1, score * (1.0 - ?))
                   WHERE score > 0.1""",
                (decay_rate,)
            )
            affected += conn.total_changes
        except Exception:
            pass

    return affected


def get_memory_stats() -> dict:
    """Get memory statistics with importance scores."""
    stats = {
        "total_memories": 0,
        "avg_score": 0.0,
        "high_importance": 0,
        "low_importance": 0,
        "stale_memories": 0,
    }

    with get_connection() as conn:
        # Total memories
        try:
            row = conn.execute("SELECT COUNT(*) as cnt FROM memory_events").fetchone()
            stats["total_memories"] = row["cnt"]
        except Exception:
            pass

        # Average score
        try:
            row = conn.execute(
                "SELECT AVG(score) as avg_score FROM memory_events"
            ).fetchone()
            stats["avg_score"] = row["avg_score"] or 0.0
        except Exception:
            pass

        # High importance (score > 0.7)
        try:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM memory_events WHERE score > 0.7"
            ).fetchone()
            stats["high_importance"] = row["cnt"]
        except Exception:
            pass

        # Low importance (score < 0.3)
        try:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM memory_events WHERE score < 0.3"
            ).fetchone()
            stats["low_importance"] = row["cnt"]
        except Exception:
            pass

        # Stale (not accessed in 30 days)
        try:
            cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM memory_events WHERE last_accessed < ?",
                (cutoff,)
            ).fetchone()
            stats["stale_memories"] = row["cnt"]
        except Exception:
            pass

    return stats


def get_important_memories(limit: int = 10) -> list[dict]:
    """Get most important memories."""
    with get_connection() as conn:
        try:
            rows = conn.execute(
                """SELECT id, title, description, type, score, timestamp
                   FROM memory_events
                   ORDER BY score DESC
                   LIMIT ?""",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []


def get_stale_memories(days: int = 30) -> list[dict]:
    """Get memories that haven't been accessed recently."""
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

    with get_connection() as conn:
        try:
            rows = conn.execute(
                """SELECT id, title, description, type, score, timestamp
                   FROM memory_events
                   WHERE last_accessed < ? OR last_accessed IS NULL
                   ORDER BY score ASC
                   LIMIT 20""",
                (cutoff,)
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []


def consolidate_memories() -> dict:
    """Consolidate similar memories by merging."""
    merged = 0
    kept = 0

    with get_connection() as conn:
        # Find potential duplicates (same title, similar content)
        try:
            rows = conn.execute(
                """SELECT id, title, description, score
                   FROM memory_events
                   WHERE title IN (
                       SELECT title FROM memory_events
                       GROUP BY title
                       HAVING COUNT(*) > 1
                   )
                   ORDER BY title, score DESC"""
            ).fetchall()

            # Group by title
            groups = {}
            for r in rows:
                title = r["title"]
                if title not in groups:
                    groups[title] = []
                groups[title].append(dict(r))

            # Merge each group
            for title, items in groups.items():
                if len(items) <= 1:
                    continue

                # Keep highest score, delete others
                best = items[0]
                for item in items[1:]:
                    try:
                        conn.execute(
                            "DELETE FROM memory_events WHERE id = ?",
                            (item["id"],)
                        )
                        merged += 1
                    except Exception:
                        pass

                kept += 1

        except Exception:
            pass

    return {"merged": merged, "kept": kept}


def score_memory(memory_id: int) -> float:
    """Calculate and update score for a specific memory."""
    with get_connection() as conn:
        try:
            row = conn.execute(
                """SELECT id, created_at, last_accessed, score
                   FROM memory_events WHERE id = ?""",
                (memory_id,)
            ).fetchone()

            if not row:
                return 0.0

            # Calculate access count from interactions
            access_count = 0
            try:
                acc_row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM memory_interactions WHERE memory_id = ?",
                    (memory_id,)
                ).fetchone()
                access_count = acc_row["cnt"]
            except Exception:
                pass

            score = calculate_importance_score(
                access_count=access_count,
                created_at=row["created_at"],
            )

            # Update score
            conn.execute(
                "UPDATE memory_events SET score = ? WHERE id = ?",
                (score, memory_id)
            )

            return score

        except Exception:
            return 0.0
