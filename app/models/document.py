from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Document:
    id: str
    path: str  # relative to root, forward-slash
    name: str
    extension: str
    mime_type: str
    size: int
    content_hash: str
    created_at: datetime
    modified_at: datetime
    indexed_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "indexed"  # indexed | error | pending
