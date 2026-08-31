from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ChatSession:
    id: str
    title: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ChatMessage:
    id: str
    session_id: str
    role: str  # user | assistant
    content: str
    created_at: datetime = field(default_factory=datetime.utcnow)
