from __future__ import annotations

from pathlib import Path

from app.git.repo import (
    find_git_root,
    get_repo_info,
    get_commits,
    get_diff,
    GitCommit,
)
from app.database.sqlite import get_connection
from app.utils.hashing import sha256_text

import logging

logger = logging.getLogger(__name__)


def index_git_history(path: Path, max_commits: int = 50) -> int:
    """Index git commit history into the database.

    Returns the number of commits indexed.
    """
    root = find_git_root(path)
    if not root:
        logger.info("No git repo found at %s", path)
        return 0

    commits = get_commits(path, max_count=max_commits)
    if not commits:
        return 0

    indexed = 0
    with get_connection() as conn:
        for commit in commits:
            # Check if already indexed
            existing = conn.execute(
                "SELECT id FROM documents WHERE path = ?",
                (f".git/commit/{commit.hash}",),
            ).fetchone()
            if existing:
                continue

            doc_id = f"git_{commit.short_hash}"
            content = _build_commit_content(commit, root)

            conn.execute(
                """INSERT OR REPLACE INTO documents
                   (id, path, hash, mime_type, size_bytes, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    doc_id,
                    f".git/commit/{commit.hash}",
                    sha256_text(content),
                    "text/x-git-commit",
                    len(content.encode()),
                    commit.date,
                    commit.date,
                ),
            )

            # Add single chunk for the commit
            chunk_id = f"{doc_id}_0000"
            conn.execute(
                """INSERT OR REPLACE INTO chunks
                   (id, document_id, content, chunk_index, start_offset, end_offset, section_title)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    chunk_id,
                    doc_id,
                    content,
                    0,
                    0,
                    len(content),
                    f"Commit {commit.short_hash}",
                ),
            )

            indexed += 1

    return indexed


def _build_commit_content(commit: GitCommit, repo_root: Path) -> str:
    """Build searchable text content from a git commit."""
    parts = [
        f"Commit: {commit.short_hash}",
        f"Author: {commit.author} <{commit.email}>",
        f"Date: {commit.date}",
        f"Message: {commit.message}",
    ]

    if commit.files_changed > 0:
        parts.append(f"Files changed: {commit.files_changed}")
    if commit.insertions > 0:
        parts.append(f"Insertions: +{commit.insertions}")
    if commit.deletions > 0:
        parts.append(f"Deletions: -{commit.deletions}")

    # Get the diff summary
    diff = get_diff(repo_root, commit.hash, max_lines=50)
    if diff:
        parts.append(f"\nChanged files:\n{diff}")

    return "\n".join(parts)


def get_git_stats(path: Path) -> dict:
    """Get git repository statistics."""
    root = find_git_root(path)
    if not root:
        return {"is_git": False}

    repo = get_repo_info(path)
    commits = get_commits(path, max_count=1000)

    # Count indexed git commits
    with get_connection() as conn:
        indexed = conn.execute(
            "SELECT COUNT(*) FROM documents WHERE path LIKE '.git/commit/%'"
        ).fetchone()[0]

    # Collect unique authors
    authors = set()
    for c in commits:
        authors.add(c.author)

    return {
        "is_git": True,
        "root": str(repo.root) if repo else None,
        "branch": repo.branch if repo else None,
        "remote_url": repo.remote_url,
        "total_commits": repo.total_commits if repo else 0,
        "indexed_commits": indexed,
        "unique_authors": list(authors),
    }
