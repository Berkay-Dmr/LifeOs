from __future__ import annotations

import re
import uuid
from pathlib import Path
from datetime import datetime

from app.database.sqlite import get_connection

import logging

logger = logging.getLogger(__name__)


def extract_dependencies(file_path: str, content: str) -> list[dict]:
    """Extract code dependencies from file content."""
    deps = []
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".py":
        deps = _extract_python_deps(content, file_path)
    elif ext in (".js", ".ts", ".jsx", ".tsx"):
        deps = _extract_js_deps(content, file_path)
    elif ext == ".go":
        deps = _extract_go_deps(content, file_path)

    return deps


def _extract_python_deps(content: str, file_path: str) -> list[dict]:
    """Extract Python dependencies."""
    deps = []

    # Import statements
    import_patterns = [
        (r"from\s+([\w.]+)\s+import", "imports"),
        (r"import\s+([\w.]+)", "imports"),
    ]

    for pattern, dep_type in import_patterns:
        for match in re.finditer(pattern, content):
            module = match.group(1)
            deps.append({
                "source_file": file_path,
                "target_module": module,
                "dependency_type": dep_type,
            })

    # Function calls (simple detection)
    call_pattern = r"(\w+)\s*\("
    for match in re.finditer(call_pattern, content):
        func_name = match.group(1)
        if func_name[0].isupper():  # Class instantiation
            deps.append({
                "source_file": file_path,
                "target_module": func_name,
                "dependency_type": "calls",
            })

    return deps


def _extract_js_deps(content: str, file_path: str) -> list[dict]:
    """Extract JavaScript/TypeScript dependencies."""
    deps = []

    # Import/require statements
    patterns = [
        (r"import\s+.*from\s+['\"](.+?)['\"]", "imports"),
        (r"require\s*\(\s*['\"](.+?)['\"]", "imports"),
        (r"import\s+['\"](.+?)['\"]", "imports"),
    ]

    for pattern, dep_type in patterns:
        for match in re.finditer(pattern, content):
            module = match.group(1)
            deps.append({
                "source_file": file_path,
                "target_module": module,
                "dependency_type": dep_type,
            })

    return deps


def _extract_go_deps(content: str, file_path: str) -> list[dict]:
    """Extract Go dependencies."""
    deps = []

    # Import statements
    pattern = r'import\s+(?:\(\s*)?(?:"(.+?)"|([\w.]+))(?:\s*\))'
    for match in re.finditer(pattern, content):
        module = match.group(1) or match.group(2)
        deps.append({
            "source_file": file_path,
            "target_module": module,
            "dependency_type": "imports",
        })

    return deps


def store_dependencies(file_path: str, deps: list[dict]) -> None:
    """Store dependencies in database."""
    with get_connection() as conn:
        # Remove old deps for this file
        conn.execute(
            "DELETE FROM code_dependencies WHERE file_path = ?",
            (file_path,)
        )

        # Insert new deps
        for dep in deps:
            dep_id = str(uuid.uuid4())[:12]
            conn.execute(
                """INSERT INTO code_dependencies
                   (id, file_path, function_name, calls_function, calls_file, dependency_type)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    dep_id,
                    dep["source_file"],
                    dep.get("function_name", ""),
                    dep["target_module"],
                    dep.get("target_file", ""),
                    dep["dependency_type"],
                ),
            )


def index_file_dependencies(file_path: str) -> int:
    """Index dependencies for a single file."""
    try:
        path = Path(file_path)
        if not path.exists():
            return 0

        content = path.read_text(encoding="utf-8", errors="ignore")
        deps = extract_dependencies(file_path, content)
        store_dependencies(file_path, deps)
        return len(deps)

    except Exception as e:
        logger.error("Failed to index deps for %s: %s", file_path, e)
        return 0


def index_directory_dependencies(root_path: str) -> int:
    """Index dependencies for all code files in a directory."""
    root = Path(root_path)
    total = 0

    code_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".go"}

    for file in root.rglob("*"):
        if file.suffix.lower() in code_extensions:
            count = index_file_dependencies(str(file))
            total += count

    return total


def get_file_dependencies(file_path: str) -> list[dict]:
    """Get all dependencies for a file."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM code_dependencies
               WHERE file_path = ?
               ORDER BY dependency_type""",
            (file_path,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_file_dependents(file_path: str) -> list[dict]:
    """Get all files that depend on this file."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM code_dependencies
               WHERE calls_file = ? OR calls_function IN (
                   SELECT function_name FROM code_dependencies WHERE file_path = ?
               )""",
            (file_path, file_path)
        ).fetchall()
        return [dict(r) for r in rows]


def search_dependencies(query: str) -> list[dict]:
    """Search dependencies by module/function name."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM code_dependencies
               WHERE calls_function LIKE ? OR calls_file LIKE ? OR file_path LIKE ?
               LIMIT 20""",
            (f"%{query}%", f"%{query}%", f"%{query}%")
        ).fetchall()
        return [dict(r) for r in rows]


def get_dependency_graph(file_path: str, depth: int = 2) -> dict:
    """Build a dependency graph starting from a file."""
    graph = {"nodes": [], "edges": []}
    visited = set()

    def _traverse(path: str, current_depth: int):
        if path in visited or current_depth > depth:
            return
        visited.add(path)

        deps = get_file_dependencies(path)
        for dep in deps:
            target = dep["calls_function"] or dep["calls_file"]
            if target:
                graph["nodes"].append({"id": target, "type": dep["dependency_type"]})
                graph["edges"].append({"source": path, "target": target})

    _traverse(file_path, 0)
    return graph
