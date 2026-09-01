from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QLabel, QFrame, QPushButton, QScrollArea, QSizePolicy,
    QTextBrowser,
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread

import logging

logger = logging.getLogger(__name__)


class AnswerCard(QFrame):
    """AI answer card with sources."""

    def __init__(self, answer: str, sources: list, parent=None):
        super().__init__(parent)
        self.setObjectName("answerCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)

        header = QLabel("AI Answer")
        header.setObjectName("titleLabel")
        font = header.font()
        font.setPointSize(14)
        header.setFont(font)
        layout.addWidget(header)

        answer_browser = QTextBrowser()
        answer_browser.setOpenExternalLinks(True)
        answer_browser.setHtml(answer)
        answer_browser.setMinimumHeight(80)
        answer_browser.setMaximumHeight(400)
        layout.addWidget(answer_browser)

        if sources:
            sources_label = QLabel("Kaynaklar:")
            sources_label.setStyleSheet("font-weight: bold; color: #7aa2f7; margin-top: 8px;")
            layout.addWidget(sources_label)

            for i, src in enumerate(sources[:5], 1):
                if hasattr(src, "path"):
                    path = src.path
                    score = src.score
                else:
                    path = src.get("path", "unknown")
                    score = src.get("score", 0)
                src_text = f"[{i}] {path} (score: {score:.0%})"
                src_label = QLabel(src_text)
                src_label.setStyleSheet("color: #9ece6a; font-size: 12px; padding-left: 12px;")
                layout.addWidget(src_label)


class AskWorker(QThread):
    """Background thread for AI ask operation."""
    finished = Signal(str, list)  # answer, sources
    error = Signal(str)  # error message

    def __init__(self, question: str):
        super().__init__()
        self.question = question

    def run(self):
        try:
            from app.config.settings import get_settings
            from app.database.sqlite import init_db
            from app.search.hybrid import hybrid_search
            from app.ai.context_builder import build_context
            from app.models.search import SearchQuery
            from app.ai.base import AIRequest

            settings = get_settings()
            init_db(settings.db_path)

            sq = SearchQuery(text=self.question, top_k=8)
            search_results = hybrid_search(sq, settings)

            if not search_results:
                self.finished.emit("No relevant information found in your knowledge base.", [])
                return

            context = build_context(search_results)

            # Try Gemini first
            answer_text = None
            try:
                from app.ai.factory import get_ai_provider
                provider = get_ai_provider(provider="gemini", api_key=settings.gemini_api_key)
                request = AIRequest(question=self.question, context=context)
                response = provider.generate(request)
                answer_text = response.answer
            except Exception as e:
                logger.warning("Gemini failed: %s", e)

            # Try OpenAI if Gemini failed
            if not answer_text:
                try:
                    from app.ai.factory import get_ai_provider
                    provider = get_ai_provider(provider="openai", api_key=settings.openai_api_key)
                    request = AIRequest(question=self.question, context=context)
                    response = provider.generate(request)
                    answer_text = response.answer
                except Exception as e:
                    logger.warning("OpenAI failed: %s", e)

            if answer_text:
                self.finished.emit(answer_text, search_results)
            else:
                source_text = "<b>AI mevcut degil.</b> En alakali kaynaklar:<br><br>"
                for i, r in enumerate(search_results[:5], 1):
                    path = r.path
                    text = r.snippet[:200] if r.snippet else ""
                    source_text += f"<b>[{i}] {path}</b><br>{text}<br><br>"
                self.finished.emit(source_text, search_results)

        except Exception as e:
            logger.error("Ask failed: %s", e)
            self.error.emit(str(e))


class AskWidget(QWidget):
    """Ask AI page widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        title = QLabel("Ask AI")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        subtitle = QLabel("Ask questions about your files and get AI-powered answers with sources")
        subtitle.setObjectName("subtitleLabel")
        layout.addWidget(subtitle)

        ask_layout = QHBoxLayout()
        ask_layout.setSpacing(8)

        self.ask_input = QLineEdit()
        self.ask_input.setObjectName("askInput")
        self.ask_input.setPlaceholderText("What do you want to know?")
        self.ask_input.returnPressed.connect(self._on_ask)
        ask_layout.addWidget(self.ask_input)

        self.ask_btn = QPushButton("Ask")
        self.ask_btn.setObjectName("primaryBtn")
        self.ask_btn.clicked.connect(self._on_ask)
        ask_layout.addWidget(self.ask_btn)

        layout.addLayout(ask_layout)

        self.status_label = QLabel("")
        self.status_label.setObjectName("subtitleLabel")
        layout.addWidget(self.status_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(12)
        self.results_layout.addStretch()

        scroll.setWidget(self.results_container)
        layout.addWidget(scroll)

    def _on_ask(self):
        question = self.ask_input.text().strip()
        if not question:
            return
        if self._worker and self._worker.isRunning():
            return

        self.ask_btn.setEnabled(False)
        self.status_label.setText("Dusunuyor...")
        self._worker = AskWorker(question)
        self._worker.finished.connect(self._on_answer)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_answer(self, answer: str, sources: list):
        self.ask_btn.setEnabled(True)
        self._show_answer(answer, sources)

    def _on_error(self, error: str):
        self.ask_btn.setEnabled(True)
        self._show_answer(f"Hata: {error}", [])

    def _show_answer(self, answer: str, sources: list):
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not answer.startswith("<"):
            answer_html = f"<p>{answer.replace(chr(10), '<br>')}</p>"
        else:
            answer_html = answer

        card = AnswerCard(answer_html, sources)
        self.results_layout.insertWidget(self.results_layout.count() - 1, card)
        self.status_label.setText("")

    def set_status(self, text: str):
        self.status_label.setText(text)
