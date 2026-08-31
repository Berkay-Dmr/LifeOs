from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Memory:
    id: str
    type: str  # fact | preference | project | problem | solution | person | concept | event | decision
    content: str
    confidence: float = 1.0
    source_count: int = 0
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
