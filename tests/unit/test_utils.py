from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from app.utils.hashing import sha256_file, sha256_text
from app.utils.text import truncate, clean_whitespace, count_tokens_approx


class TestSha256Text:
    def test_basic_hash(self):
        result = sha256_text("hello")
        assert len(result) == 64  # SHA256 hex digest

    def test_deterministic(self):
        assert sha256_text("test") == sha256_text("test")

    def test_different_inputs(self):
        assert sha256_text("abc") != sha256_text("def")

    def test_unicode(self):
        result = sha256_text("öğrenci numarası")
        assert len(result) == 64


class TestSha256File:
    def test_file_hash(self, tmp_dir):
        test_file = tmp_dir / "test.txt"
        test_file.write_text("hello world", encoding="utf-8")

        result = sha256_file(test_file)
        assert len(result) == 64

    def test_same_content_same_hash(self, tmp_dir):
        f1 = tmp_dir / "a.txt"
        f2 = tmp_dir / "b.txt"
        f1.write_text("same content", encoding="utf-8")
        f2.write_text("same content", encoding="utf-8")

        assert sha256_file(f1) == sha256_file(f2)

    def test_different_content_different_hash(self, tmp_dir):
        f1 = tmp_dir / "a.txt"
        f2 = tmp_dir / "b.txt"
        f1.write_text("content A", encoding="utf-8")
        f2.write_text("content B", encoding="utf-8")

        assert sha256_file(f1) != sha256_file(f2)


class TestTruncate:
    def test_short_text_unchanged(self):
        assert truncate("hello", 10) == "hello"

    def test_long_text_truncated(self):
        result = truncate("hello world this is long", 10)
        assert len(result) == 10
        assert result.endswith("...")

    def test_exact_length(self):
        assert truncate("12345", 5) == "12345"


class TestCleanWhitespace:
    def test_single_spaces(self):
        assert clean_whitespace("hello world") == "hello world"

    def test_multiple_spaces(self):
        assert clean_whitespace("hello   world") == "hello world"

    def test_newlines(self):
        assert clean_whitespace("hello\n\nworld") == "hello world"

    def test_leading_trailing(self):
        assert clean_whitespace("  hello  ") == "hello"


class TestCountTokensApprox:
    def test_empty(self):
        assert count_tokens_approx("") == 0

    def test_short_text(self):
        assert count_tokens_approx("test") == 1  # 4 chars / 4

    def test_longer_text(self):
        assert count_tokens_approx("hello world") == 2  # 11 chars / 4 = 2.75 -> 2
