from __future__ import annotations

import os
from pathlib import Path, PurePosixPath, PureWindowsPath


def normalize_path(path: Path) -> str:
    """Return a forward-slash path string for consistent storage."""
    return path.as_posix()


def relative_to_root(file_path: Path, root: Path) -> str | None:
    """Return file path relative to root directory, or None if outside."""
    try:
        rel = file_path.relative_to(root)
        return normalize_path(rel)
    except ValueError:
        return None


def is_relative_to(child: Path, parent: Path) -> bool:
    """Check if child is inside parent (Python 3.9+ compatible)."""
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def expand_user(path_str: str) -> Path:
    return Path(os.path.expanduser(path_str)).resolve()
