from __future__ import annotations

from datetime import datetime

import pytest

from app.database.sqlite import init_db, get_connection
from app.database.repositories import (
    insert_document, get_document_by_id, get_document_by_path,
    delete_document, list_documents, count_documents, document_exists,
    insert_chunk, get_chunks_for_document, get_all_chunks, count_chunks,
    delete_chunks_for_document,
)
from app.models.document import Document
from app.models.chunk import Chunk


class TestDocuments:
    def test_insert_and_get(self, tmp_db):
        doc = Document(
            id="doc1", path="test/file.txt", name="file.txt",
            extension=".txt", mime_type="text/plain", size=100,
            content_hash="hash1",
            created_at=datetime(2024, 1, 1),
            modified_at=datetime(2024, 6, 1),
        )
        insert_document(doc)
        result = get_document_by_id("doc1")
        assert result is not None
        assert result.name == "file.txt"
        assert result.path == "test/file.txt"

    def test_get_by_path(self, tmp_db):
        doc = Document(
            id="doc2", path="docs/readme.md", name="readme.md",
            extension=".md", mime_type="text/markdown", size=200,
            content_hash="hash2",
            created_at=datetime(2024, 1, 1),
            modified_at=datetime(2024, 6, 1),
        )
        insert_document(doc)
        result = get_document_by_path("docs/readme.md")
        assert result is not None
        assert result.id == "doc2"

    def test_delete(self, tmp_db):
        doc = Document(
            id="doc3", path="delete_me.txt", name="delete_me.txt",
            extension=".txt", mime_type="text/plain", size=50,
            content_hash="hash3",
            created_at=datetime(2024, 1, 1),
            modified_at=datetime(2024, 6, 1),
        )
        insert_document(doc)
        assert document_exists("delete_me.txt")

        delete_document("doc3")
        assert not document_exists("delete_me.txt")

    def test_list_documents(self, tmp_db):
        for i in range(3):
            doc = Document(
                id=f"doc_list_{i}", path=f"file_{i}.txt", name=f"file_{i}.txt",
                extension=".txt", mime_type="text/plain", size=100,
                content_hash=f"hash_{i}",
                created_at=datetime(2024, 1, 1),
                modified_at=datetime(2024, 6, i + 1),
            )
            insert_document(doc)

        docs = list_documents()
        assert len(docs) >= 3

    def test_count(self, tmp_db):
        initial = count_documents()
        doc = Document(
            id="doc_count", path="count.txt", name="count.txt",
            extension=".txt", mime_type="text/plain", size=10,
            content_hash="hash_count",
            created_at=datetime(2024, 1, 1),
            modified_at=datetime(2024, 6, 1),
        )
        insert_document(doc)
        assert count_documents() == initial + 1


class TestChunks:
    def test_insert_and_get(self, tmp_db):
        # First insert a document
        doc = Document(
            id="doc_chunk", path="chunk_test.txt", name="chunk_test.txt",
            extension=".txt", mime_type="text/plain", size=100,
            content_hash="hash_chunk",
            created_at=datetime(2024, 1, 1),
            modified_at=datetime(2024, 6, 1),
        )
        insert_document(doc)

        chunk = Chunk(
            id="chunk1", document_id="doc_chunk",
            text="Test chunk content",
            start_offset=0, end_offset=20,
            page=1, section="Intro",
        )
        insert_chunk(chunk)

        chunks = get_chunks_for_document("doc_chunk")
        assert len(chunks) >= 1
        assert chunks[0].text == "Test chunk content"

    def test_count_chunks(self, tmp_db):
        initial = count_chunks()
        doc = Document(
            id="doc_count_c", path="count_c.txt", name="count_c.txt",
            extension=".txt", mime_type="text/plain", size=10,
            content_hash="hash_count_c",
            created_at=datetime(2024, 1, 1),
            modified_at=datetime(2024, 6, 1),
        )
        insert_document(doc)

        chunk = Chunk(
            id="chunk_count", document_id="doc_count_c",
            text="Count me", start_offset=0, end_offset=8,
        )
        insert_chunk(chunk)
        assert count_chunks() == initial + 1

    def test_delete_chunks_for_document(self, tmp_db):
        doc = Document(
            id="doc_del_c", path="del_c.txt", name="del_c.txt",
            extension=".txt", mime_type="text/plain", size=10,
            content_hash="hash_del_c",
            created_at=datetime(2024, 1, 1),
            modified_at=datetime(2024, 6, 1),
        )
        insert_document(doc)

        for i in range(3):
            chunk = Chunk(
                id=f"chunk_del_{i}", document_id="doc_del_c",
                text=f"Chunk {i}", start_offset=i * 10, end_offset=(i + 1) * 10,
            )
            insert_chunk(chunk)

        assert len(get_chunks_for_document("doc_del_c")) >= 3
        delete_chunks_for_document("doc_del_c")
        assert len(get_chunks_for_document("doc_del_c")) == 0
