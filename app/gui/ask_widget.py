from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QLabel, QFrame, QPushButton, QScrollArea, QSizePolicy,
    QTextBrowser, QListWidget, QListWidgetItem, QSplitter,
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont

import logging

logger = logging.getLogger(__name__)


class AnswerCard(QFrame):
    """Single message card (user or assistant)."""

    def __init__(self, role: str, content: str, sources: list = None, parent=None):
        super().__init__(parent)
        self.setObjectName("answerCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)

        # Role label
        role_label = QLabel("Sen" if role == "user" else "AI")
        role_label.setStyleSheet(
            "font-weight: bold; color: #7aa2f7;" if role == "assistant"
            else "font-weight: bold; color: #9ece6a;"
        )
        layout.addWidget(role_label)

        # Content
        content_browser = QTextBrowser()
        content_browser.setOpenExternalLinks(True)
        if content.startswith("<"):
            content_browser.setHtml(content)
        else:
            content_browser.setHtml(f"<p>{content.replace(chr(10), '<br>')}</p>")
        content_browser.setMinimumHeight(40)
        content_browser.setMaximumHeight(300)
        content_browser.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(content_browser)

        # Sources (only for assistant)
        if sources and role == "assistant":
            sources_label = QLabel("Kaynaklar:")
            sources_label.setStyleSheet("font-weight: bold; color: #7aa2f7; margin-top: 4px; font-size: 11px;")
            layout.addWidget(sources_label)

            for i, src in enumerate(sources[:5], 1):
                if hasattr(src, "path"):
                    path = src.path
                    score = src.score
                else:
                    path = src.get("path", "unknown")
                    score = src.get("score", 0)
                src_text = f"[{i}] {path} ({score:.0%})"
                src_label = QLabel(src_text)
                src_label.setStyleSheet("color: #9ece6a; font-size: 11px; padding-left: 12px;")
                layout.addWidget(src_label)


class AskWorker(QThread):
    """Background thread for AI ask operation."""
    finished = Signal(str, list)
    error = Signal(str)

    def __init__(self, question: str, chat_history: list):
        super().__init__()
        self.question = question
        self.chat_history = chat_history

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
                self.finished.emit("Bu konuda indekslenmiş yeterli bilgi bulamadım.", [])
                return

            context = build_context(search_results)

            answer_text = None
            try:
                from app.ai.factory import get_ai_provider
                provider = get_ai_provider(provider="gemini", api_key=settings.gemini_api_key)
                request = AIRequest(
                    question=self.question,
                    context=context,
                    chat_history=self.chat_history,
                )
                response = provider.generate(request)
                answer_text = response.answer
            except Exception as e:
                logger.warning("Gemini failed: %s", e)

            if not answer_text:
                try:
                    from app.ai.factory import get_ai_provider
                    provider = get_ai_provider(provider="openai", api_key=settings.openai_api_key)
                    request = AIRequest(
                        question=self.question,
                        context=context,
                        chat_history=self.chat_history,
                    )
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
    """Ask AI page with conversation history."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._current_session_id = None
        self._chat_history = []  # [{role, content}, ...]
        self._init_ui()
        self._load_sessions()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title bar
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(32, 16, 32, 8)

        title = QLabel("Ask AI")
        title.setObjectName("titleLabel")
        title_bar.addWidget(title)
        title_bar.addStretch()

        new_chat_btn = QPushButton("+ Yeni Sohbet")
        new_chat_btn.setObjectName("primaryBtn")
        new_chat_btn.clicked.connect(self._new_session)
        title_bar.addWidget(new_chat_btn)

        layout.addLayout(title_bar)

        # Main content: sidebar + chat
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        # Left sidebar: session list
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("QFrame { border-right: 1px solid #333; }")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)

        sidebar_label = QLabel("Sohbetler")
        sidebar_label.setStyleSheet("font-weight: bold; color: #7aa2f7; padding: 4px;")
        sidebar_layout.addWidget(sidebar_label)

        self.session_list = QListWidget()
        self.session_list.setStyleSheet("QListWidget { border: none; }")
        self.session_list.currentRowChanged.connect(self._on_session_selected)
        sidebar_layout.addWidget(self.session_list)

        delete_btn = QPushButton("Sil")
        delete_btn.clicked.connect(self._delete_session)
        sidebar_layout.addWidget(delete_btn)

        splitter.addWidget(sidebar)

        # Right: chat area
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(16, 8, 16, 8)
        chat_layout.setSpacing(8)

        # Chat scroll
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_layout.setSpacing(8)
        self.chat_layout.addStretch()

        self.chat_scroll.setWidget(self.chat_container)
        chat_layout.addWidget(self.chat_scroll)

        # Input bar
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.ask_input = QLineEdit()
        self.ask_input.setObjectName("askInput")
        self.ask_input.setPlaceholderText("Sorunuzu yazın...")
        self.ask_input.returnPressed.connect(self._on_ask)
        input_layout.addWidget(self.ask_input)

        self.ask_btn = QPushButton("Gönder")
        self.ask_btn.setObjectName("primaryBtn")
        self.ask_btn.clicked.connect(self._on_ask)
        input_layout.addWidget(self.ask_btn)

        chat_layout.addLayout(input_layout)

        splitter.addWidget(chat_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

    def _load_sessions(self):
        """Load session list from DB."""
        from app.database.repositories import get_chat_history
        from app.database.sqlite import get_connection

        self.session_list.clear()
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, title FROM chat_sessions ORDER BY updated_at DESC"
            ).fetchall()
            for row in rows:
                item = QListWidgetItem(row["title"])
                item.setData(Qt.UserRole, row["id"])
                self.session_list.addItem(item)

    def _new_session(self):
        """Start a new chat session."""
        self._current_session_id = None
        self._chat_history = []
        self._clear_chat()
        self.ask_input.setFocus()

    def _on_session_selected(self, row: int):
        """Load a previous session."""
        if row < 0:
            return
        item = self.session_list.item(row)
        if not item:
            return

        session_id = item.data(Qt.UserRole)
        self._current_session_id = session_id
        self._chat_history = []

        self._clear_chat()

        from app.database.repositories import get_chat_history
        messages = get_chat_history(session_id)

        for msg in messages:
            self._chat_history.append({"role": msg.role, "content": msg.content})
            self._add_message_card(msg.role, msg.content)

    def _delete_session(self):
        """Delete selected session."""
        item = self.session_list.currentItem()
        if not item:
            return
        session_id = item.data(Qt.UserRole)

        from app.database.sqlite import get_connection
        with get_connection() as conn:
            conn.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))

        self._load_sessions()
        self._new_session()

    def _clear_chat(self):
        """Clear chat display."""
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_ask(self):
        question = self.ask_input.text().strip()
        if not question:
            return
        if self._worker and self._worker.isRunning():
            return

        # Create session if needed
        if not self._current_session_id:
            from app.database.repositories import create_chat_session
            title = question[:50] + ("..." if len(question) > 50 else "")
            session = create_chat_session(title)
            self._current_session_id = session.id
            self._load_sessions()

        # Save user message
        from app.database.repositories import add_chat_message
        add_chat_message(self._current_session_id, "user", question)
        self._chat_history.append({"role": "user", "content": question})

        # Show user message
        self._add_message_card("user", question)

        # Clear input
        self.ask_input.clear()
        self.ask_btn.setEnabled(False)

        # Start AI worker
        self._worker = AskWorker(question, self._chat_history[:-1])  # history without current
        self._worker.finished.connect(self._on_answer)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_answer(self, answer: str, sources: list):
        self.ask_btn.setEnabled(True)

        # Save assistant message
        from app.database.repositories import add_chat_message
        add_chat_message(self._current_session_id, "assistant", answer)
        self._chat_history.append({"role": "assistant", "content": answer})

        # Show assistant message
        self._add_message_card("assistant", answer, sources)

    def _on_error(self, error: str):
        self.ask_btn.setEnabled(True)
        self._add_message_card("assistant", f"Hata: {error}")

    def _add_message_card(self, role: str, content: str, sources: list = None):
        card = AnswerCard(role, content, sources)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, card)

        # Scroll to bottom
        sb = self.chat_scroll.verticalScrollBar()
        sb.setValue(sb.maximum())
