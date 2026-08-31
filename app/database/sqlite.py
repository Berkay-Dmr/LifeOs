from __future__ import annotations

import sqlite3
from pathlib import Path
from contextlib import contextmanager

from app.utils.logging import setup_logging

import logging

logger = logging.getLogger(__name__)

_DB_PATH: Path | None = None


def init_db(db_path: Path) -> None:
    global _DB_PATH
    _DB_PATH = db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        _run_migrations(conn)
    logger.info("Database initialized at %s", db_path)


def get_db_path() -> Path:
    if _DB_PATH is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _DB_PATH


@contextmanager
def get_connection():
    path = get_db_path()
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _run_migrations(conn: sqlite3.Connection) -> None:
    from app.database.migrations import MIGRATIONS

    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='_migrations'"
    )
    if cursor.fetchone() is None:
        conn.execute(
            "CREATE TABLE _migrations (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
        )

    applied = {
        row[0]
        for row in conn.execute("SELECT name FROM _migrations").fetchall()
    }

    for migration_name, sql in MIGRATIONS:
        if migration_name not in applied:
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO _migrations (name) VALUES (?)", (migration_name,)
            )
            logger.info("Applied migration: %s", migration_name)
