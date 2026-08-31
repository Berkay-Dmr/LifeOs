from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QLabel, QFrame, QPushButton, QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

import logging

logger = logging.getLogger(__name__)


class ResultCard(QFrame):
    """A single search result card."""

    def __init__(self, title: str, snippet: str, score: float, source: str, parent=None):
        super().__init__(parent)
        self.setObjectName("resultCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(16, 12, 16, 12)

        # Header row
        header = QHBoxLayout()
        header.setSpacing(12)

        score_label = QLabel(f"{score:.0%}")
        score_label.setObjectName("scoreLabel")
        score_label.setFixedWidth(40)
        header.addWidget(score_label)

        source_label = QLabel(source)
        source_label.setObjectName("sourceLabel")
        header.addWidget(source_label)

        header.addStretch()
        layout.addLayout(header)

        # Title
        title_lbl = QLabel(title)
        title_lbl.setWordWrap(True)
        font = title_lbl.font()
        font.setBold(True)
        font.setPointSize(11)
        title_lbl.setFont(font)
        layout.addWidget(title_lbl)

        # Snippet
        if snippet:
            snippet_lbl = QLabel(snippet[:300])
            snippet_lbl.setWordWrap(True)
            snippet_lbl.setStyleSheet("color: #787c99; font-size: 12px;")
            layout.addWidget(snippet_lbl)


class SearchWidget(QWidget):
    """Search page widget."""

    result_clicked = Signal(str)  # file path

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results: list = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("Search")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        subtitle = QLabel("Search across all your indexed files")
        subtitle.setObjectName("subtitleLabel")
        layout.addWidget(subtitle)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Search your knowledge base...")
        self.search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self.search_input)

        search_btn = QPushButton("Search")
        search_btn.setObjectName("primaryBtn")
        search_btn.clicked.connect(self._on_search)
        search_layout.addWidget(search_btn)

        layout.addLayout(search_layout)

        # Results count
        self.count_label = QLabel("")
        self.count_label.setObjectName("subtitleLabel")
        layout.addWidget(self.count_label)

        # Results area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(8)
        self.results_layout.addStretch()

        scroll.setWidget(self.results_container)
        layout.addWidget(scroll)

    def _on_search(self):
        query = self.search_input.text().strip()
        if not query:
            return

        self.count_label.setText("Searching...")
        QTimer.singleShot(10, lambda: self._do_search(query))

    def _do_search(self, query: str):
        try:
            from app.config.settings import get_settings
            from app.database.sqlite import init_db
            from app.search.hybrid import hybrid_search
            from app.models.search import SearchQuery

            settings = get_settings()
            init_db(settings.db_path)

            sq = SearchQuery(text=query, top_k=15)
            results = hybrid_search(sq, settings)
            self._show_results(results)

        except Exception as e:
            logger.error("Search failed: %s", e)
            self.count_label.setText(f"Search failed: {e}")

    def _show_results(self, results: list):
        # Clear old results
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._results = results
        self.count_label.setText(f"{len(results)} results found")

        for r in results:
            # Support both SearchResult dataclass and dict
            if hasattr(r, "path"):
                path = r.path
                text = r.snippet or ""
                score = r.score
            else:
                path = r.get("path", "unknown")
                text = r.get("text", "")
                score = r.get("score", 0.0)

            card = ResultCard(
                title=path.split("/")[-1].split("\\")[-1],
                snippet=text[:300],
                score=score,
                source=path,
            )
            card.mousePressEvent = lambda e, p=path: self.result_clicked.emit(p)
            self.results_layout.insertWidget(self.results_layout.count() - 1, card)

    def set_status(self, text: str):
        self.count_label.setText(text)
