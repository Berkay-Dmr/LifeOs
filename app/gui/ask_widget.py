from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QLabel, QFrame, QPushButton, QScrollArea, QSizePolicy,
    QTextBrowser, QListWidget, QListWidgetItem, QSplitter,
    QComboBox,
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont

from app.gui.auto_complete import AutoCompleteLineEdit

import logging

logger = logging.getLogger(__name__)


class AnswerCard(QFrame):
    """Single message card (user or assistant)."""

    def __init__(self, role: str, content: str, sources: list = None, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        if role == "assistant":
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #1a1535, stop:1 #1e1840);
                    border: 1px solid rgba(187,154,247,0.3);
                    border-radius: 14px;
                    padding: 16px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #152015, stop:1 #182818);
                    border: 1px solid rgba(158,206,106,0.3);
                    border-radius: 14px;
                    padding: 16px;
                }
            """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)

        # Role badge
        if role == "assistant":
            role_label = QLabel("AI")
            role_label.setStyleSheet("""
                QLabel {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #bb9af7, stop:1 #9a7af7);
                    color: white;
                    border-radius: 6px;
                    padding: 2px 8px;
                    font-weight: bold;
                    font-size: 11px;
                }
            """)
        else:
            role_label = QLabel("You")
            role_label.setStyleSheet("""
                QLabel {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #9ece6a, stop:1 #80b855);
                    color: #1a1b26;
                    border-radius: 6px;
                    padding: 2px 8px;
                    font-weight: bold;
                    font-size: 11px;
                }
            """)
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
            sources_frame = QFrame()
            sources_frame.setStyleSheet("""
                QFrame {
                    background: rgba(122,162,247,0.1);
                    border-radius: 8px;
                    padding: 8px;
                }
            """)
            sources_layout = QVBoxLayout(sources_frame)
            sources_layout.setContentsMargins(8, 6, 8, 6)
            sources_layout.setSpacing(4)

            sources_label = QLabel("Sources:")
            sources_label.setStyleSheet("font-weight: bold; color: #7aa2f7; font-size: 11px; background: transparent;")
            sources_layout.addWidget(sources_label)

            for i, src in enumerate(sources[:5], 1):
                if hasattr(src, "path"):
                    path = src.path
                    score = src.score
                else:
                    path = src.get("path", "unknown")
                    score = src.get("score", 0)
                src_text = f"[{i}] {path.split('/')[-1].split(chr(92))[-1]} ({score:.0%})"
                src_label = QLabel(src_text)
                src_label.setStyleSheet("color: #9ece6a; font-size: 11px; background: transparent;")
                sources_layout.addWidget(src_label)

            layout.addWidget(sources_frame)


class AskWorker(QThread):
    """Background thread for AI ask operation."""
    finished = Signal(str, list)
    error = Signal(str)

    def __init__(self, question: str, chat_history: list, file_type: str = None):
        super().__init__()
        self.question = question
        self.chat_history = chat_history
        self.file_type = file_type

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

            sq = SearchQuery(text=self.question, top_k=8, file_type=self.file_type)
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
        self._chat_history = []
        self._init_ui()
        self._load_sessions()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title bar
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(36, 20, 36, 12)

        title = QLabel("Ask AI")
        title.setObjectName("titleLabel")
        title_bar.addWidget(title)

        title_bar.addStretch()

        new_chat_btn = QPushButton("+ New Chat")
        new_chat_btn.setObjectName("primaryBtn")
        new_chat_btn.setCursor(Qt.PointingHandCursor)
        new_chat_btn.clicked.connect(self._new_session)
        title_bar.addWidget(new_chat_btn)

        layout.addLayout(title_bar)

        # Main content
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)

        # Left sidebar: session list
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QFrame {
                background: rgba(18,18,42,0.8);
                border-right: 1px solid #2a2a4a;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)

        sidebar_label = QLabel("Chats")
        sidebar_label.setStyleSheet("""
            font-weight: bold;
            color: #7aa2f7;
            padding: 4px;
            font-size: 12px;
        """)
        sidebar_layout.addWidget(sidebar_label)

        self.session_list = QListWidget()
        self.session_list.setStyleSheet("""
            QListWidget {
                border: none;
                background: transparent;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 8px;
                margin: 2px 0;
            }
            QListWidget::item:hover {
                background: rgba(122,162,247,0.15);
            }
            QListWidget::item:selected {
                background: rgba(122,162,247,0.25);
                color: #e0e0f0;
            }
        """)
        self.session_list.currentRowChanged.connect(self._on_session_selected)
        sidebar_layout.addWidget(self.session_list)

        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("dangerBtn")
        delete_btn.setCursor(Qt.PointingHandCursor)
        sidebar_layout.addWidget(delete_btn)

        splitter.addWidget(sidebar)

        # Right: chat area
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(20, 12, 20, 12)
        chat_layout.setSpacing(12)

        # Chat scroll
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_layout.setSpacing(12)
        self.chat_layout.addStretch()

        self.chat_scroll.setWidget(self.chat_container)
        chat_layout.addWidget(self.chat_scroll)

        # Input bar
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background: rgba(26,26,53,0.8);
                border: 1px solid #2a2a50;
                border-radius: 16px;
                padding: 8px;
            }
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setSpacing(10)
        input_layout.setContentsMargins(12, 8, 12, 8)

        self.file_filter = QComboBox()
        self.file_filter.addItems(["All", "PDF", "Document", "Code", "Image"])
        self.file_filter.setFixedWidth(100)
        input_layout.addWidget(self.file_filter)

        self.ask_input = AutoCompleteLineEdit()
        self.ask_input.setObjectName("askInput")
        self.ask_input.setPlaceholderText("Ask anything about your files...")
        self.ask_input.returnPressed.connect(self._on_ask)
        input_layout.addWidget(self.ask_input)

        self.ask_btn = QPushButton("Send")
        self.ask_btn.setObjectName("primaryBtn")
        self.ask_btn.setCursor(Qt.PointingHandCursor)
        self.ask_btn.clicked.connect(self._on_ask)
        input_layout.addWidget(self.ask_btn)

        chat_layout.addWidget(input_frame)

        splitter.addWidget(chat_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

    def _load_sessions(self):
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
        self._current_session_id = None
        self._chat_history = []
        self._clear_chat()
        self.ask_input.setFocus()

    def _on_session_selected(self, row: int):
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

        filter_map = {0: None, 1: "pdf", 2: "doc", 3: "code", 4: "image"}
        file_type = filter_map.get(self.file_filter.currentIndex())

        if not self._current_session_id:
            from app.database.repositories import create_chat_session
            title = question[:50] + ("..." if len(question) > 50 else "")
            session = create_chat_session(title)
            self._current_session_id = session.id
            self._load_sessions()

        from app.database.repositories import add_chat_message
        add_chat_message(self._current_session_id, "user", question)
        self._chat_history.append({"role": "user", "content": question})

        self._add_message_card("user", question)

        self.ask_input.clear()
        self.ask_btn.setEnabled(False)
        self.ask_btn.setText("Thinking...")

        self._worker = AskWorker(question, self._chat_history[:-1], file_type)
        self._worker.finished.connect(self._on_answer)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_answer(self, answer: str, sources: list):
        self.ask_btn.setEnabled(True)
        self.ask_btn.setText("Send")

        from app.database.repositories import add_chat_message
        add_chat_message(self._current_session_id, "assistant", answer)
        self._chat_history.append({"role": "assistant", "content": answer})

        self._add_message_card("assistant", answer, sources)

    def _on_error(self, error: str):
        self.ask_btn.setEnabled(True)
        self.ask_btn.setText("Send")
        self._add_message_card("assistant", f"Error: {error}")

    def _add_message_card(self, role: str, content: str, sources: list = None):
        card = AnswerCard(role, content, sources)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, card)

        sb = self.chat_scroll.verticalScrollBar()
        sb.setValue(sb.maximum())
