from __future__ import annotations

import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import pytest


@pytest.fixture
def tmp_dir():
    """Create a temporary directory for test files."""
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def tmp_db(tmp_dir):
    """Create a temporary database for tests."""
    from app.database.sqlite import init_db, _run_migrations

    db_path = tmp_dir / "test.db"
    init_db(db_path)
    yield db_path


@pytest.fixture
def sample_document():
    """Create a sample Document object."""
    from app.models.document import Document

    return Document(
        id="test_doc_001",
        path="test/sample.txt",
        name="sample.txt",
        extension=".txt",
        mime_type="text/plain",
        size=1024,
        content_hash="abc123def456",
        created_at=datetime(2024, 1, 1),
        modified_at=datetime(2024, 6, 15),
    )


@pytest.fixture
def sample_chunk():
    """Create a sample Chunk object."""
    from app.models.chunk import Chunk

    return Chunk(
        id="test_chunk_001",
        document_id="test_doc_001",
        text="This is a test chunk with some content for testing.",
        start_offset=0,
        end_offset=50,
        page=1,
        section="Introduction",
    )


@pytest.fixture
def sample_memory():
    """Create a sample Memory object."""
    from app.models.memory import Memory

    return Memory(
        id="test_mem_001",
        type="fact",
        content="Test memory content for unit testing",
        confidence=0.95,
        source_count=2,
    )
