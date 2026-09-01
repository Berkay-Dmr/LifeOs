from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout,
    QGraphicsOpacityEffect, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QFont

import logging

logger = logging.getLogger(__name__)


class ToastNotification(QWidget):
    """Floating toast notification widget."""

    def __init__(self, message: str, level: str = "info", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(320)

        # Style based on level
        colors = {
            "info": ("#7aa2f7", "rgba(122,162,247,0.15)"),
            "success": ("#9ece6a", "rgba(158,206,106,0.15)"),
            "warning": ("#e0af68", "rgba(224,175,104,0.15)"),
            "error": ("#f7768e", "rgba(247,118,142,0.15)"),
        }
        border_color, bg_color = colors.get(level, colors["info"])

        self.setStyleSheet(f"""
            QWidget {{
                background: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(10)

        # Icon
        icons = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}
        icon_label = QLabel(icons.get(level, "ℹ️"))
        icon_label.setStyleSheet("font-size: 16px; background: transparent;")
        layout.addWidget(icon_label)

        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"""
            color: {border_color};
            font-size: 12px;
            font-weight: bold;
            background: transparent;
        """)
        layout.addWidget(msg_label)

        # Opacity effect for animation
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity)

    def show_at(self, x: int, y: int):
        """Show toast at position with animation."""
        self.move(x, y)
        self.show()
        self.raise_()

        # Fade out after 3 seconds
        QTimer.singleShot(3000, self._fade_out)

    def _fade_out(self):
        self._anim = QPropertyAnimation(self._opacity, b"opacity")
        self._anim.setDuration(500)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.InQuad)
        self._anim.finished.connect(self.deleteLater)
        self._anim.start()


class NotificationManager:
    """Manages toast notifications for the application."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._toasts = []
        return cls._instance

    def __init__(self):
        self._parent = None

    def set_parent(self, parent: QWidget):
        self._parent = parent

    def show(self, message: str, level: str = "info"):
        """Show a toast notification."""
        if self._parent is None:
            logger.info("Notification [%s]: %s", level, message)
            return

        toast = ToastNotification(message, level, self._parent)

        # Position at top-right of parent
        parent_rect = self._parent.geometry()
        x = parent_rect.x() + parent_rect.width() - 340
        y = parent_rect.y() + 20

        # Stack multiple toasts
        for existing in self._toasts:
            if existing.isVisible():
                y += 50

        toast.show_at(x, y)
        self._toasts.append(toast)

    def info(self, message: str):
        self.show(message, "info")

    def success(self, message: str):
        self.show(message, "success")

    def warning(self, message: str):
        self.show(message, "warning")

    def error(self, message: str):
        self.show(message, "error")


# Global instance
notifications = NotificationManager()
