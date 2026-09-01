from __future__ import annotations

import pytest

from app.extractors.text import TextExtractor
from app.extractors.markdown import MarkdownExtractor
from app.extractors.code import CodeExtractor


class TestTextExtractor:
    def test_extract_txt(self, tmp_dir):
        test_file = tmp_dir / "test.txt"
        test_file.write_text("Hello world\nLine 2\nLine 3", encoding="utf-8")

        extractor = TextExtractor()
        result = extractor.extract(test_file)
        assert len(result.chunks) > 0
        all_text = " ".join(c.text for c in result.chunks)
        assert "Hello world" in all_text

    def test_empty_file(self, tmp_dir):
        test_file = tmp_dir / "empty.txt"
        test_file.write_text("", encoding="utf-8")

        extractor = TextExtractor()
        result = extractor.extract(test_file)
        # Empty file may have 0 chunks or 1 empty chunk
        if result.chunks:
            assert result.chunks[0].text.strip() == ""

    def test_encoding(self, tmp_dir):
        test_file = tmp_dir / "turkish.txt"
        test_file.write_text("Öğrenci numarası: 25181616071", encoding="utf-8")

        extractor = TextExtractor()
        result = extractor.extract(test_file)
        all_text = " ".join(c.text for c in result.chunks)
        assert "Öğrenci" in all_text


class TestMarkdownExtractor:
    def test_extract_md(self, tmp_dir):
        test_file = tmp_dir / "readme.md"
        test_file.write_text("# Title\n\nSome content\n\n## Section\n\nMore content", encoding="utf-8")

        extractor = MarkdownExtractor()
        result = extractor.extract(test_file)
        all_text = " ".join(c.text for c in result.chunks)
        assert "Title" in all_text

    def test_preserves_structure(self, tmp_dir):
        test_file = tmp_dir / "doc.md"
        test_file.write_text("# H1\n## H2\nParagraph", encoding="utf-8")

        extractor = MarkdownExtractor()
        result = extractor.extract(test_file)
        all_text = " ".join(c.text for c in result.chunks)
        assert "H1" in all_text


class TestCodeExtractor:
    def test_extract_python(self, tmp_dir):
        test_file = tmp_dir / "app.py"
        test_file.write_text("def hello():\n    print('hi')", encoding="utf-8")

        extractor = CodeExtractor()
        result = extractor.extract(test_file)
        all_text = " ".join(c.text for c in result.chunks)
        assert "hello" in all_text

    def test_extract_javascript(self, tmp_dir):
        test_file = tmp_dir / "app.js"
        test_file.write_text("function hello() {\n  console.log('hi');\n}", encoding="utf-8")

        extractor = CodeExtractor()
        result = extractor.extract(test_file)
        all_text = " ".join(c.text for c in result.chunks)
        assert "hello" in all_text

    def test_preserves_code(self, tmp_dir):
        test_file = tmp_dir / "calc.py"
        code = "def add(a, b):\n    return a + b"
        test_file.write_text(code, encoding="utf-8")

        extractor = CodeExtractor()
        result = extractor.extract(test_file)
        all_text = " ".join(c.text for c in result.chunks)
        assert "return a + b" in all_text
