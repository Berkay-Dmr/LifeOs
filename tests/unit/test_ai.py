from __future__ import annotations

import pytest

from app.ai.context_builder import build_context, extract_source_references
from app.ai.prompts import build_rag_prompt, build_rag_prompt_with_history, SYSTEM_PROMPT
from app.models.search import SearchResult


@pytest.fixture
def sample_results():
    return [
        SearchResult(
            document_id="doc1",
            chunk_id="chunk1",
            title="sample.txt",
            path="test/sample.txt",
            snippet="This is test content about Python programming.",
            score=0.85,
            page=1,
            section="Introduction",
        ),
        SearchResult(
            document_id="doc2",
            chunk_id="chunk2",
            title="notes.md",
            path="docs/notes.md",
            snippet="Some notes about machine learning.",
            score=0.72,
            page=3,
        ),
    ]


class TestBuildContext:
    def test_builds_context_string(self, sample_results):
        context = build_context(sample_results)
        assert "test/sample.txt" in context
        assert "test content about Python" in context

    def test_includes_page_numbers(self, sample_results):
        context = build_context(sample_results)
        assert "sayfa 1" in context

    def test_empty_results(self):
        context = build_context([])
        assert context == ""

    def test_max_chunks_limit(self, sample_results):
        context = build_context(sample_results, max_chunks=1)
        assert "test/sample.txt" in context
        assert "notes.md" not in context


class TestExtractSourceReferences:
    def test_extracts_references(self, sample_results):
        refs = extract_source_references(sample_results)
        assert len(refs) == 2
        assert "test/sample.txt" in refs[0]

    def test_includes_page(self, sample_results):
        refs = extract_source_references(sample_results)
        assert "sayfa 1" in refs[0]

    def test_includes_section(self, sample_results):
        refs = extract_source_references(sample_results)
        assert "Introduction" in refs[0]


class TestBuildRagPrompt:
    def test_contains_question(self):
        prompt = build_rag_prompt("What is Python?", "context here")
        assert "What is Python?" in prompt

    def test_contains_context(self):
        prompt = build_rag_prompt("question", "This is the context")
        assert "This is the context" in prompt

    def test_has_sources_header(self):
        prompt = build_rag_prompt("q", "c")
        assert "SOURCES:" in prompt


class TestBuildRagPromptWithHistory:
    def test_without_history(self):
        prompt = build_rag_prompt_with_history("q", "c", [])
        assert "q" in prompt
        assert "c" in prompt

    def test_with_history(self):
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        prompt = build_rag_prompt_with_history("q", "c", history)
        assert "Hello" in prompt
        assert "Hi there!" in prompt
        assert "q" in prompt


class TestSystemPrompt:
    def test_exists(self):
        assert len(SYSTEM_PROMPT) > 0

    def test_mentions_lifeos(self):
        assert "LifeOS" in SYSTEM_PROMPT

    def test_mentions_sources(self):
        assert "sources" in SYSTEM_PROMPT.lower()
