from __future__ import annotations

from PySide6.QtWidgets import (
    QLineEdit, QListWidget, QListWidgetItem, QWidget,
    QVBoxLayout, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint
from PySide6.QtGui import QFont

import logging

logger = logging.getLogger(__name__)


class AutoCompletePopup(QFrame):
    """Dropdown popup for auto-complete suggestions."""

    suggestion_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setFixedWidth(350)
        self.setMaximumHeight(250)
        self.setStyleSheet("""
            QFrame {
                background: #161b22;
                border: 1px solid #30363d;
                border-radius: 10px;
            }
            QListWidget {
                border: none;
                background: transparent;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-radius: 6px;
                margin: 2px 4px;
                color: #c9d1d9;
            }
            QListWidget::item:hover {
                background: rgba(56,139,253,0.2);
            }
            QListWidget::item:selected {
                background: #388bfd;
                color: #ffffff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)

        self.list_widget = QListWidget()
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_widget.currentRowChanged.connect(self._on_row_changed)
        layout.addWidget(self.list_widget)

        self._suggestions: list[str] = []

    def show_suggestions(self, suggestions: list[str], target: QLineEdit):
        """Show suggestions near the target widget."""
        if not suggestions:
            self.hide()
            return

        self._suggestions = suggestions
        self.list_widget.clear()

        for s in suggestions[:8]:
            item = QListWidgetItem(s)
            self.list_widget.addItem(item)

        self.list_widget.setCurrentRow(0)

        # Position below the target widget
        global_pos = target.mapToGlobal(QPoint(0, target.height()))
        self.move(global_pos)
        self.show()
        self.raise_()

    def _on_row_changed(self, row: int):
        if 0 <= row < len(self._suggestions):
            self.suggestion_selected.emit(self._suggestions[row])

    def key_press_event(self, event):
        """Forward key events to list widget."""
        self.list_widget.keyPressEvent(event)


class AutoCompleteLineEdit(QLineEdit):
    """QLineEdit with auto-complete functionality."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._popup = AutoCompletePopup(self)
        self._popup.suggestion_selected.connect(self._on_suggestion_selected)
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(800)
        self._timer.timeout.connect(self._fetch_suggestions)

        self.textChanged.connect(self._on_text_changed)
        self._popup.list_widget.installEventFilter(self)
        self._user_is_selecting = False
        self._rejected_for_query: str = ""
        self._last_shown_query: str = ""

    def _on_text_changed(self, text: str):
        if self._user_is_selecting:
            return
        self._popup.hide()
        # If user changed the query significantly, reset rejection
        if self._rejected_for_query and not text.startswith(self._rejected_for_query):
            self._rejected_for_query = ""
        if len(text) >= 5:
            self._timer.start()
        else:
            self._timer.stop()

    def _fetch_suggestions(self):
        """Fetch suggestions based on current text."""
        text = self.text().strip()
        if len(text) < 5:
            self._popup.hide()
            return

        # Don't show again for the same rejected query
        if text == self._rejected_for_query:
            return

        # Don't show if already shown for this exact query
        if text == self._last_shown_query:
            return

        suggestions = self._get_suggestions(text)
        if suggestions and len(suggestions) > 1:
            self._last_shown_query = text
            self._popup.show_suggestions(suggestions, self)
        else:
            self._popup.hide()

    def _on_popup_rejected(self):
        """Mark current query as rejected."""
        self._rejected_for_query = self.text().strip()

    def _get_suggestions(self, query: str) -> list[str]:
        """Get suggestions from search history and document names."""
        prefix_matches = []
        contains_matches = []
        seen = set()
        query_lower = query.lower()

        # 1. Search history
        history = self._get_search_history()
        for item in history:
            if item in seen:
                continue
            item_lower = item.lower()
            if item_lower.startswith(query_lower):
                prefix_matches.append(item)
                seen.add(item)
            elif query_lower in item_lower:
                contains_matches.append(item)
                seen.add(item)

        # 2. Document names
        doc_names = self._get_document_names()
        for name in doc_names:
            if name in seen:
                continue
            name_lower = name.lower()
            if name_lower.startswith(query_lower):
                prefix_matches.append(name)
                seen.add(name)
            elif query_lower in name_lower:
                contains_matches.append(name)
                seen.add(name)

        # 3. Entity names
        entities = self._get_entities()
        for entity in entities:
            if entity in seen:
                continue
            entity_lower = entity.lower()
            if entity_lower.startswith(query_lower):
                prefix_matches.append(entity)
                seen.add(entity)
            elif query_lower in entity_lower:
                contains_matches.append(entity)
                seen.add(entity)

        # Prefix matches first, then contains
        all_suggestions = prefix_matches + contains_matches
        return all_suggestions[:6]

    def _get_search_history(self) -> list[str]:
        """Get recent search queries from chat sessions."""
        try:
            from app.database.sqlite import get_connection
            with get_connection() as conn:
                rows = conn.execute(
                    "SELECT DISTINCT title FROM chat_sessions ORDER BY updated_at DESC LIMIT 50"
                ).fetchall()
                return [r["title"] for r in rows]
        except Exception:
            return []

    def _get_document_names(self) -> list[str]:
        """Get indexed document names."""
        try:
            from app.database.sqlite import get_connection
            with get_connection() as conn:
                rows = conn.execute(
                    "SELECT DISTINCT name FROM documents LIMIT 100"
                ).fetchall()
                return [r["name"] for r in rows]
        except Exception:
            return []

    def _get_entities(self) -> list[str]:
        """Get extracted entities."""
        try:
            from app.database.sqlite import get_connection
            with get_connection() as conn:
                rows = conn.execute(
                    "SELECT DISTINCT name FROM entities LIMIT 100"
                ).fetchall()
                return [r["name"] for r in rows]
        except Exception:
            return []

    def _on_suggestion_selected(self, suggestion: str):
        self._user_is_selecting = True
        self.setText(suggestion)
        self._user_is_selecting = False
        self._popup.hide()
        self.setFocus()

    def eventFilter(self, obj, event):
        """Filter events for the popup list widget."""
        if obj == self._popup.list_widget:
            if event.type() == event.Type.KeyPress:
                if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                    current = self._popup.list_widget.currentItem()
                    if current:
                        self._on_suggestion_selected(current.text())
                        return True
                elif event.key() == Qt.Key_Escape:
                    self._on_popup_rejected()
                    self._popup.hide()
                    return True
                elif event.key() == Qt.Key_Down:
                    row = self._popup.list_widget.currentRow()
                    if row < self._popup.list_widget.count() - 1:
                        self._popup.list_widget.setCurrentRow(row + 1)
                    return True
                elif event.key() == Qt.Key_Up:
                    row = self._popup.list_widget.currentRow()
                    if row > 0:
                        self._popup.list_widget.setCurrentRow(row - 1)
                    return True
            elif event.type() == event.Type.FocusOut:
                self._on_popup_rejected()
                QTimer.singleShot(200, self._check_hide_popup)
        return super().eventFilter(obj, event)

    def _check_hide_popup(self):
        """Check if popup should be hidden."""
        if not self._popup.isActiveWindow() and not self.hasFocus():
            self._popup.hide()

    def focusOutEvent(self, event):
        if self._popup.isVisible():
            self._on_popup_rejected()
        super().focusOutEvent(event)
        QTimer.singleShot(200, self._check_hide_popup)
