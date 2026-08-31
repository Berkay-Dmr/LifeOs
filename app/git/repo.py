from __future__ import annotations

import subprocess
from pathlib import Path
from dataclasses import dataclass

import logging

logger = logging.getLogger(__name__)


@dataclass
class GitRepo:
    root: Path
    branch: str
    remote_url: str | None
    total_commits: int


@dataclass
class GitCommit:
    hash: str
    short_hash: str
    author: str
    email: str
    date: str
    message: str
    files_changed: int
    insertions: int
    deletions: int


def find_git_root(path: Path) -> Path | None:
    """Walk up to find .git directory."""
    current = path.resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return None


def is_git_repo(path: Path) -> bool:
    """Check if path is inside a git repository."""
    return find_git_root(path) is not None


def get_repo_info(path: Path) -> GitRepo | None:
    """Get basic git repo information."""
    root = find_git_root(path)
    if not root:
        return None

    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(root), capture_output=True, text=True, timeout=10
        ).stdout.strip()

        remote_url = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=str(root), capture_output=True, text=True, timeout=10
        ).stdout.strip() or None

        total = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=str(root), capture_output=True, text=True, timeout=10
        ).stdout.strip()

        return GitRepo(
            root=root,
            branch=branch,
            remote_url=remote_url,
            total_commits=int(total) if total.isdigit() else 0,
        )
    except Exception as e:
        logger.warning("Failed to get git info: %s", e)
        return None


def get_commits(
    path: Path,
    max_count: int = 50,
    since: str | None = None,
) -> list[GitCommit]:
    """Get recent commits from the repo."""
    root = find_git_root(path)
    if not root:
        return []

    fmt = "%H|%h|%an|%ae|%ai|%s"
    cmd = ["git", "log", f"--format={fmt}", f"--max-count={max_count}"]
    if since:
        cmd.append(f"--since={since}")

    try:
        result = subprocess.run(
            cmd, cwd=str(root), capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return []

        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 5)
            if len(parts) < 6:
                continue

            # Get file stats for this commit
            stats = _get_commit_stats(root, parts[0])

            commits.append(GitCommit(
                hash=parts[0],
                short_hash=parts[1],
                author=parts[2],
                email=parts[3],
                date=parts[4][:10],
                message=parts[5],
                files_changed=stats[0],
                insertions=stats[1],
                deletions=stats[2],
            ))

        return commits
    except Exception as e:
        logger.warning("Failed to get commits: %s", e)
        return []


def _get_commit_stats(repo_root: Path, commit_hash: str) -> tuple[int, int, int]:
    """Get files changed, insertions, deletions for a commit."""
    try:
        result = subprocess.run(
            ["git", "diff", "--shortstat", f"{commit_hash}~1", commit_hash],
            cwd=str(repo_root), capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return (0, 0, 0)

        line = result.stdout.strip()
        files = ins = dels = 0

        if "file" in line:
            import re
            f_match = re.search(r"(\d+) file", line)
            i_match = re.search(r"(\d+) insertion", line)
            d_match = re.search(r"(\d+) deletion", line)
            if f_match:
                files = int(f_match.group(1))
            if i_match:
                ins = int(i_match.group(1))
            if d_match:
                dels = int(d_match.group(1))

        return (files, ins, dels)
    except Exception:
        return (0, 0, 0)


def get_diff(repo_root: Path, commit_hash: str, max_lines: int = 200) -> str:
    """Get the diff for a specific commit."""
    try:
        result = subprocess.run(
            ["git", "show", "--stat", "--format=", commit_hash],
            cwd=str(repo_root), capture_output=True, text=True, timeout=15
        )
        lines = result.stdout.strip().split("\n")[:max_lines]
        return "\n".join(lines)
    except Exception:
        return ""
