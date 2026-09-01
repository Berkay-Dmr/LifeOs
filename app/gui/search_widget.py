from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QLabel, QFrame, QPushButton, QScrollArea, QSizePolicy,
    QButtonGroup, QDateEdit, QComboBox,
)
from PySide6.QtCore import Qt, Signal, QThread, QDate
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

        title_lbl = QLabel(title)
        title_lbl.setWordWrap(True)
        font = title_lbl.font()
        font.setBold(True)
        font.setPointSize(11)
        title_lbl.setFont(font)
        layout.addWidget(title_lbl)

        if snippet:
            snippet_lbl = QLabel(snippet[:300])
            snippet_lbl.setWordWrap(True)
            snippet_lbl.setStyleSheet("color: #787c99; font-size: 12px;")
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
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(12)

        title = QLabel("Search")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Search your knowledge base...")
        self.search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self.search_input)

        self.search_btn = QPushButton("Search")
        self.search_btn.setObjectName("primaryBtn")
        self.search_btn.clicked.connect(self._on_search)
        search_layout.addWidget(self.search_btn)

        layout.addLayout(search_layout)

        # File type filter buttons
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(4)

        filter_label = QLabel("Tur:")
        filter_label.setStyleSheet("color: #787c99; font-size: 12px;")
        filter_layout.addWidget(filter_label)

        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)

        filters = [
            ("Tumu", None),
            ("PDF", "pdf"),
            ("Belge", "doc"),
            ("Kod", "code"),
            ("Gorsel", "image"),
        ]

        for label, value in filters:
            btn = QPushButton(label)
            btn.setCheckable(True)
            if value is None:
                btn.setChecked(True)
            btn.setStyleSheet(
                "QPushButton { padding: 4px 12px; border-radius: 4px; font-size: 12px; }"
                "QPushButton:checked { background: #7aa2f7; color: white; }"
                "QPushButton:!checked { background: #333; color: #aaa; }"
            )
            self.filter_group.addButton(btn, id=filters.index((label, value)))
            btn.clicked.connect(lambda checked, v=value: self._set_filter(v))
            filter_layout.addWidget(btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Advanced filters (collapsible)
        advanced_frame = QFrame()
        advanced_frame.setStyleSheet("QFrame { border: 1px solid #333; border-radius: 4px; padding: 8px; }")
        advanced_layout = QVBoxLayout(advanced_frame)
        advanced_layout.setSpacing(8)

        advanced_title = QLabel("Gelismisi Filtreler")
        advanced_title.setStyleSheet("font-weight: bold; color: #7aa2f7; font-size: 12px;")
        advanced_layout.addWidget(advanced_title)

        # Date range
        date_layout = QHBoxLayout()
        date_layout.setSpacing(8)

        date_from_label = QLabel("Baslangic:")
        date_from_label.setStyleSheet("font-size: 12px;")
        date_layout.addWidget(date_from_label)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setDate(self.date_from.date().addYears(-1))
        self.date_from.setStyleSheet("font-size: 12px;")
        date_layout.addWidget(self.date_from)

        date_to_label = QLabel("Bitis:")
        date_to_label.setStyleSheet("font-size: 12px;")
        date_layout.addWidget(date_to_label)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setStyleSheet("font-size: 12px;")
        date_layout.addWidget(self.date_to)

        date_layout.addStretch()
        advanced_layout.addLayout(date_layout)

        # Filename search
        filename_layout = QHBoxLayout()
        filename_layout.setSpacing(8)

        filename_label = QLabel("Dosya adi:")
        filename_label.setStyleSheet("font-size: 12px;")
        filename_layout.addWidget(filename_label)

        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("Dosya adinda ara...")
        self.filename_input.setStyleSheet("font-size: 12px;")
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
        self.results_layout.setSpacing(8)
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

        # Get advanced filters
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")
        filename = self.filename_input.text().strip() or None

        self.search_btn.setEnabled(False)
        self.count_label.setText("Araniyor...")
        self._worker = SearchWorker(
            query,
            self._current_filter,
            date_from=date_from,
            date_to=date_to,
            filename=filename,
        )
        self._worker.finished.connect(self._on_results)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_results(self, results: list):
        self.search_btn.setEnabled(True)
        self._show_results(results)

    def _on_error(self, error: str):
        self.search_btn.setEnabled(True)
        self.count_label.setText(f"Hata: {error}")

    def _show_results(self, results: list):
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._results = results
        filter_text = f" ({self._current_filter})" if self._current_filter else ""
        self.count_label.setText(f"{len(results)} sonuc bulundu{filter_text}")

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
