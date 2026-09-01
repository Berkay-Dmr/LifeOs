from __future__ import annotations

import pytest

from app.chunking.text_chunker import TextChunker
from app.chunking.code_chunker import CodeChunker


class TestTextChunker:
    def test_short_text_single_chunk(self):
        chunker = TextChunker(max_tokens=800)
        text = "This is a short text."
        chunks = chunker.chunk(text)
        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_empty_text(self):
        chunker = TextChunker(max_tokens=800)
        chunks = chunker.chunk("")
        assert len(chunks) == 0

    def test_whitespace_only(self):
        chunker = TextChunker(max_tokens=800)
        chunks = chunker.chunk("   \n\n  ")
        assert len(chunks) == 0

    def test_long_text_multiple_chunks(self):
        chunker = TextChunker(max_tokens=100)  # ~400 chars
        text = "A" * 1000  # 1000 chars = ~250 tokens
        chunks = chunker.chunk(text)
        assert len(chunks) > 1

    def test_chunks_have_offsets(self):
        chunker = TextChunker(max_tokens=100)
        text = "A" * 1000
        chunks = chunker.chunk(text)
        for chunk in chunks:
            assert chunk.start_offset >= 0
            assert chunk.end_offset > chunk.start_offset

    def test_paragraph_break(self):
        chunker = TextChunker(max_tokens=20)  # ~80 chars
        text = "First paragraph content here.\n\nSecond paragraph content here.\n\nThird paragraph content here."
        chunks = chunker.chunk(text)
        assert len(chunks) >= 2

    def test_sentence_break(self):
        chunker = TextChunker(max_tokens=50)  # ~200 chars
        text = "Sentence one. Sentence two. Sentence three. " * 10
        chunks = chunker.chunk(text)
        assert len(chunks) >= 2


class TestCodeChunker:
    def test_short_code_single_chunk(self):
        chunker = CodeChunker(max_tokens=800)
        code = "def hello():\n    print('hi')"
        chunks = chunker.chunk(code)
        assert len(chunks) == 1

    def test_empty_code(self):
        chunker = CodeChunker(max_tokens=800)
        chunks = chunker.chunk("")
        assert len(chunks) == 0

    def test_long_code_multiple_chunks(self):
        chunker = CodeChunker(max_tokens=50)  # ~200 chars
        code = "\n\n".join([f"def func_{i}():\n    return {i}" for i in range(20)])
        chunks = chunker.chunk(code)
        assert len(chunks) > 1

    def test_code_blocks_split(self):
        chunker = CodeChunker(max_tokens=20)  # ~80 chars
        code = """def alpha_function():
    pass

def beta_function():
    pass

def gamma_function():
    pass"""
        chunks = chunker.chunk(code)
        assert len(chunks) >= 2
