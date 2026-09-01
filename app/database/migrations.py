from __future__ import annotations

MIGRATIONS: list[tuple[str, str]] = [
    (
        "001_core_tables",
        """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    extension TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    indexed_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'indexed'
);

CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    text TEXT NOT NULL,
    start_offset INTEGER NOT NULL,
    end_offset INTEGER NOT NULL,
    page INTEGER,
    section TEXT,
    embedding_id INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    memory_id TEXT NOT NULL,
    document_id TEXT,
    chunk_id TEXT,
    source_type TEXT NOT NULL DEFAULT 'document'
);

CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    source_count INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS relations (
    id TEXT PRIMARY KEY,
    source_entity_id TEXT NOT NULL,
    target_entity_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS index_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks(embedding_id);
CREATE INDEX IF NOT EXISTS idx_sources_memory ON sources(memory_id);
CREATE INDEX IF NOT EXISTS idx_documents_path ON documents(path);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
""",
    ),
    (
        "002_projects",
        """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    language TEXT,
    framework TEXT,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_files (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    added_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS project_commits (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    commit_hash TEXT NOT NULL,
    message TEXT,
    author TEXT,
    committed_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_project_files_project ON project_files(project_id);
CREATE INDEX IF NOT EXISTS idx_project_files_document ON project_files(document_id);
CREATE INDEX IF NOT EXISTS idx_project_commits_project ON project_commits(project_id);
""",
    ),
    (
        "003_episodic_memory",
        """
CREATE TABLE IF NOT EXISTS memory_events (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    type TEXT NOT NULL,
    project_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    entities TEXT,
    source TEXT,
    confidence REAL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_memory_events_type ON memory_events(type);
CREATE INDEX IF NOT EXISTS idx_memory_events_project ON memory_events(project_id);
CREATE INDEX IF NOT EXISTS idx_memory_events_timestamp ON memory_events(timestamp);
""",
    ),
    (
        "004_decisions",
        """
CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    date TEXT NOT NULL,
    project_id TEXT,
    reason TEXT,
    alternatives TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    superseded_by TEXT,
    confidence REAL DEFAULT 1.0,
    source TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
    FOREIGN KEY (superseded_by) REFERENCES decisions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_decisions_project ON decisions(project_id);
CREATE INDEX IF NOT EXISTS idx_decisions_status ON decisions(status);
""",
    ),
    (
        "005_bugs",
        """
CREATE TABLE IF NOT EXISTS bugs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    error_message TEXT,
    project_id TEXT,
    cause TEXT,
    solution TEXT,
    resolved INTEGER DEFAULT 0,
    first_seen TEXT NOT NULL,
    resolved_at TEXT,
    confidence REAL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_bugs_project ON bugs(project_id);
CREATE INDEX IF NOT EXISTS idx_bugs_resolved ON bugs(resolved);
CREATE INDEX IF NOT EXISTS idx_bugs_error ON bugs(error_message);
""",
    ),
    (
        "006_git_memory_links",
        """
CREATE TABLE IF NOT EXISTS git_memory_links (
    id TEXT PRIMARY KEY,
    commit_hash TEXT NOT NULL,
    memory_event_id TEXT,
    decision_id TEXT,
    bug_id TEXT,
    link_type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (memory_event_id) REFERENCES memory_events(id) ON DELETE SET NULL,
    FOREIGN KEY (decision_id) REFERENCES decisions(id) ON DELETE SET NULL,
    FOREIGN KEY (bug_id) REFERENCES bugs(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_git_links_commit ON git_memory_links(commit_hash);
""",
    ),
    (
        "007_memory_interactions",
        """
CREATE TABLE IF NOT EXISTS memory_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id INTEGER NOT NULL,
    memory_type TEXT NOT NULL,
    interaction_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (memory_id) REFERENCES documents(id)
);

CREATE INDEX IF NOT EXISTS idx_memory_interactions_id ON memory_interactions(memory_id);
""",
    ),
]
