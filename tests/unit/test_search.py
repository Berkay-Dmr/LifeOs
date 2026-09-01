from __future__ import annotations

import pytest

from app.search.ranking import rank_results
from app.models.search import SearchResult
from app.config.settings import LifeOSSettings


@pytest.fixture
def settings():
    return LifeOSSettings()


@pytest.fixture
def mixed_results():
    return [
        SearchResult(
            document_id="doc1", chunk_id="c1",
            title="transkript.pdf", path="transkript.pdf",
            snippet="Öğrenci No: 25181616071",
            score=0.8, page=1,
        ),
        SearchResult(
            document_id="doc2", chunk_id="c2",
            title="sgk.pdf", path="sgk.pdf",
            snippet="Sigortalı T.C. Kimlik No: 10927166024",
            score=0.6, page=3,
        ),
        SearchResult(
            document_id="doc3", chunk_id="c3",
            title="random.txt", path="random.txt",
            snippet="This is unrelated content about weather.",
            score=0.5,
        ),
    ]


class TestRankResults:
    def test_returns_same_count(self, mixed_results, settings):
        ranked = rank_results(mixed_results, settings)
        assert len(ranked) == 3

    def test_sorted_by_score(self, mixed_results, settings):
        ranked = rank_results(mixed_results, settings)
        scores = [r.score for r in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_empty_results(self, settings):
        ranked = rank_results([], settings)
        assert ranked == []

    def test_single_result(self, settings):
        results = [
            SearchResult(
                document_id="d1", chunk_id="c1",
                title="t", path="p",
                snippet="s", score=0.5,
            )
        ]
        ranked = rank_results(results, settings)
        assert len(ranked) == 1


class TestSearchResult:
    def test_has_required_fields(self):
        r = SearchResult(
            document_id="d1", chunk_id="c1",
            title="test", path="test.txt",
            snippet="content", score=0.9,
        )
        assert r.document_id == "d1"
        assert r.score == 0.9
        assert r.page is None

    def test_optional_fields(self):
        r = SearchResult(
            document_id="d1", chunk_id="c1",
            title="t", path="p",
            snippet="s", score=0.5,
            page=5, section="Intro",
        )
        assert r.page == 5
        assert r.section == "Intro"
