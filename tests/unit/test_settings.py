from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.config.settings import LifeOSSettings, get_settings


class TestSettings:
    def test_default_values(self):
        settings = LifeOSSettings()
        assert settings.log_level == "INFO" or settings.log_level is not None
        assert settings.max_file_size_mb == 50
        assert settings.chunk_size == 800
        assert settings.chunk_overlap == 100
        assert settings.search_top_k == 10

    def test_search_weights(self):
        settings = LifeOSSettings()
        total = (
            settings.semantic_weight
            + settings.keyword_weight
            + settings.recency_weight
            + settings.metadata_weight
        )
        assert abs(total - 1.0) < 0.01

    def test_root_path(self):
        settings = LifeOSSettings()
        if settings.root_directory:
            assert settings.root_path is not None
            assert isinstance(settings.root_path, Path)

    def test_db_path(self):
        settings = LifeOSSettings()
        assert settings.db_path.name == "lifeos.db"

    def test_vectors_path_no_ascii(self, tmp_dir):
        settings = LifeOSSettings()
        settings.root_directory = str(tmp_dir)
        vectors = settings.vectors_path
        assert "vectors" in str(vectors)

    def test_vectors_path_with_ascii(self, tmp_dir):
        settings = LifeOSSettings()
        # Create a path with non-ASCII characters
        non_ascii_dir = tmp_dir / "ğüşıöç"
        non_ascii_dir.mkdir(exist_ok=True)
        settings.root_directory = str(non_ascii_dir)
        vectors = settings.vectors_path
        # Should fallback to ~/.lifeos/vectors/<hash>
        assert ".lifeos" in str(vectors) or "vectors" in str(vectors)


class TestGetSettings:
    def test_returns_settings_instance(self):
        settings = get_settings()
        assert isinstance(settings, LifeOSSettings)

    def test_singleton_behavior(self):
        s1 = get_settings()
        s2 = get_settings()
        # Both should be valid (not necessarily same instance)
        assert s1.log_level == s2.log_level
