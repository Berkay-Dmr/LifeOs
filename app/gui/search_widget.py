from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QLabel, QFrame, QPushButton, QScrollArea, QSizePolicy,
    QButtonGroup, QDateEdit, QComboBox,
)
from PySide6.QtCore import Qt, Signal, QThread, QDate
from PySide6.QtGui import QFont, QColor, QLinearGradient

import logging

logger = logging.getLogger(__name__)


class ResultCard(QFrame):
    """A single search result card with gradient styling."""

    def __init__(self, title: str, snippet: str, score: float, source: str, parent=None):
        super().__init__(parent)
        self.setObjectName("resultCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(18, 14, 18, 14)

        # Header row
        header = QHBoxLayout()
        header.setSpacing(14)

        # Score badge
        score_label = QLabel(f"{score:.0%}")
        score_label.setObjectName("scoreLabel")
        score_label.setFixedWidth(48)
        score_label.setAlignment(Qt.AlignCenter)
        score_label.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e0af68, stop:1 #ff9e64);
                color: #1a1b26;
                border-radius: 10px;
                padding: 4px;
                font-weight: bold;
                font-size: 11px;
            }}
        """)
        header.addWidget(score_label)

        # Source tag
        source_label = QLabel(source.split("/")[-1].split("\\")[-1])
        source_label.setObjectName("sourceLabel")
        header.addWidget(source_label)

        header.addStretch()
        layout.addLayout(header)

        # Title
        title_lbl = QLabel(title)
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #e0e0f0;
            padding: 2px 0;
        """)
        layout.addWidget(title_lbl)

        # Snippet
        if snippet:
            snippet_lbl = QLabel(snippet[:300])
            snippet_lbl.setWordWrap(True)
            snippet_lbl.setStyleSheet("""
                color: #8888aa;
                font-size: 12px;
                line-height: 1.4;
                padding: 4px 0;
            """)
            layout.addWidget(snippet_lbl)


class SearchWorker(QThread):
    """Background thread for search operation."""
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, query: str, file_type: str = None,
                 date_from: str = None, date_to: str = None,
                 filename: str = None):
        super().__init__()
        self.query = query
        self.file_type = file_type
        self.date_from = date_from
        self.date_to = date_to
        self.filename = filename

    def run(self):
        try:
            from app.config.settings import get_settings
            from app.database.sqlite import init_db
            from app.search.hybrid import hybrid_search
            from app.models.search import SearchQuery

            settings = get_settings()
            init_db(settings.db_path)

            sq = SearchQuery(
                text=self.query,
                top_k=15,
                file_type=self.file_type,
                date_from=self.date_from,
                date_to=self.date_to,
                filename=self.filename,
            )
            results = hybrid_search(sq, settings)
            self.finished.emit(results)

        except Exception as e:
            logger.error("Search failed: %s", e)
            self.error.emit(str(e))


class SearchWidget(QWidget):
    """Search page widget with advanced filters."""

    result_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results: list = []
        self._worker = None
        self._current_filter = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(16)

        # Title with gradient
        title = QLabel("Search Your Knowledge")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        subtitle = QLabel("Find anything across your indexed files")
        subtitle.setObjectName("subtitleLabel")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)

        from app.gui.auto_complete import AutoCompleteLineEdit
        self.search_input = AutoCompleteLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("🔍  Type to search...")
        self.search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self.search_input)

        self.search_btn = QPushButton("Search")
        self.search_btn.setObjectName("primaryBtn")
        self.search_btn.clicked.connect(self._on_search)
        search_layout.addWidget(self.search_btn)

        layout.addLayout(search_layout)

        # File type filter buttons
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background: rgba(122,162,247,0.08);
                border-radius: 12px;
                padding: 8px;
            }
        """)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setSpacing(6)
        filter_layout.setContentsMargins(12, 8, 12, 8)

        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet("color: #8888aa; font-size: 12px; background: transparent;")
        filter_layout.addWidget(filter_label)

        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)

        filters = [
            ("All", None),
            ("PDF", "pdf"),
            ("Document", "doc"),
            ("Code", "code"),
            ("Image", "image"),
        ]

        for label, value in filters:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            if value is None:
                btn.setChecked(True)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 6px 16px;
                    border-radius: 8px;
                    font-size: 12px;
                    background: transparent;
                    color: #8888aa;
                    border: 1px solid transparent;
                }
                QPushButton:hover {
                    background: rgba(122,162,247,0.1);
                    color: #c0c0e0;
                }
                QPushButton:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #7aa2f7, stop:1 #5a8af7);
                    color: white;
                    font-weight: bold;
                    border: none;
                }
            """)
            self.filter_group.addButton(btn, id=filters.index((label, value)))
            btn.clicked.connect(lambda checked, v=value: self._set_filter(v))
            filter_layout.addWidget(btn)

        filter_layout.addStretch()
        layout.addWidget(filter_frame)

        # Advanced filters (collapsible)
        advanced_frame = QFrame()
        advanced_frame.setStyleSheet("""
            QFrame {
                background: rgba(187,154,247,0.06);
                border: 1px solid rgba(187,154,247,0.2);
                border-radius: 12px;
                padding: 12px;
            }
        """)
        advanced_layout = QVBoxLayout(advanced_frame)
        advanced_layout.setSpacing(10)

        advanced_title = QLabel("Advanced Filters")
        advanced_title.setStyleSheet("""
            font-weight: bold;
            color: #bb9af7;
            font-size: 12px;
            background: transparent;
        """)
        advanced_layout.addWidget(advanced_title)

        # Date range
        date_layout = QHBoxLayout()
        date_layout.setSpacing(10)

        date_from_label = QLabel("From:")
        date_from_label.setStyleSheet("color: #8888aa; font-size: 12px; background: transparent;")
        date_layout.addWidget(date_from_label)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setDate(self.date_from.date().addYears(-1))
        date_layout.addWidget(self.date_from)

        date_to_label = QLabel("To:")
        date_to_label.setStyleSheet("color: #8888aa; font-size: 12px; background: transparent;")
        date_layout.addWidget(date_to_label)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        date_layout.addWidget(self.date_to)

        date_layout.addStretch()
        advanced_layout.addLayout(date_layout)

        # Filename search
        filename_layout = QHBoxLayout()
        filename_layout.setSpacing(10)

        filename_label = QLabel("Filename:")
        filename_label.setStyleSheet("color: #8888aa; font-size: 12px; background: transparent;")
        filename_layout.addWidget(filename_label)

        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("Search in filename...")
        self.filename_input.setStyleSheet("""
            QLineEdit {
                background: rgba(15,15,26,0.6);
                border: 1px solid #2a2a50;
                border-radius: 8px;
                padding: 6px 12px;
                color: #e0e0f0;
                min-width: 200px;
            }
            QLineEdit:focus {
                border-color: #7aa2f7;
            }
        """)
        filename_layout.addWidget(self.filename_input)

        advanced_layout.addLayout(filename_layout)

        layout.addWidget(advanced_frame)

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
        self.results_layout.setSpacing(10)
        self.results_layout.addStretch()

        scroll.setWidget(self.results_container)
        layout.addWidget(scroll)

    def _set_filter(self, file_type: str):
        self._current_filter = file_type

    def _on_search(self):
        query = self.search_input.text().strip()
        if not query:
            return
        if self._worker and self._worker.isRunning():
            return

        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")
        filename = self.filename_input.text().strip() or None

        self.search_btn.setEnabled(False)
        self.search_btn.setText("Searching...")
        self.count_label.setText("Searching across your knowledge base...")
        self._worker = SearchWorker(
            query, self._current_filter,
            date_from=date_from, date_to=date_to, filename=filename,
        )
        self._worker.finished.connect(self._on_results)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_results(self, results: list):
        self.search_btn.setEnabled(True)
        self.search_btn.setText("Search")
        self._show_results(results)

    def _on_error(self, error: str):
        self.search_btn.setEnabled(True)
        self.search_btn.setText("Search")
        self.count_label.setText(f"Error: {error}")

    def _show_results(self, results: list):
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._results = results
        filter_text = f" ({self._current_filter})" if self._current_filter else ""
        self.count_label.setText(f"{len(results)} results found{filter_text}")

        for r in results:
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
