from __future__ import annotations

from pathlib import Path
from typing import Callable

# Default directories to skip (inside root)
DEFAULT_SKIP_DIRS: set[str] = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "bin",
    "obj",
    "dist",
    "build",
    ".cache",
    ".idea",
    ".vscode",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    ".eggs",
    "*.egg-info",
    # LifeOS internal
    "data",
    "logs",
}

# Default file extensions to skip
DEFAULT_SKIP_EXTENSIONS: set[str] = {
    # Executables / binaries
    ".exe", ".dll", ".so", ".dylib", ".bin", ".dat", ".msi",
    # Archives
    ".zip", ".tar", ".gz", ".rar", ".7z", ".bz2", ".xz",
    # Media
    ".mp3", ".mp4", ".avi", ".mkv", ".mov", ".wav", ".flac",
    ".ogg", ".wma", ".m4a",
    # Images (MVP dışı — Phase 10'da eklenecek)
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".ico",
    ".svg", ".tiff", ".tif",
    # Databases
    ".db", ".sqlite", ".sqlite3", ".ldb",
    # Fonts
    ".ttf", ".otf", ".woff", ".woff2",
    # Other
    ".pyc", ".pyo", ".class", ".o", ".a",
}

# Default file names to skip
DEFAULT_SKIP_FILES: set[str] = {
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
}


def should_skip_dir(name: str, custom_skip: set[str] | None = None) -> bool:
    skip = DEFAULT_SKIP_DIRS | (custom_skip or set())
    if name in skip:
        return True
    # Match patterns like *.egg-info
    for pattern in skip:
        if pattern.startswith("*") and name.endswith(pattern[1:]):
            return True
    return False


def should_skip_file(
    path: Path,
    custom_skip_ext: set[str] | None = None,
    custom_skip_names: set[str] | None = None,
) -> bool:
    ext_skip = DEFAULT_SKIP_EXTENSIONS | (custom_skip_ext or set())
    name_skip = DEFAULT_SKIP_FILES | (custom_skip_names or set())

    if path.suffix.lower() in ext_skip:
        return True
    if path.name in name_skip:
        return True
    return False


def should_skip_path(
    path: Path,
    root: Path,
    custom_skip_dirs: set[str] | None = None,
    custom_skip_ext: set[str] | None = None,
    custom_skip_names: set[str] | None = None,
) -> bool:
    """Check if a file should be skipped based on rules."""
    if should_skip_file(path, custom_skip_ext, custom_skip_names):
        return True
    # Check if any parent directory is in skip list
    try:
        rel = path.relative_to(root)
        for part in rel.parts[:-1]:
            if should_skip_dir(part, custom_skip_dirs):
                return True
    except ValueError:
        return True
    return False
