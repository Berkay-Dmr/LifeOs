from __future__ import annotations

import sys
from typing import Callable

import logging

logger = logging.getLogger(__name__)


class SystemTray:
    """System tray icon for LifeOS."""

    def __init__(
        self,
        on_show: Callable[[], None] | None = None,
        on_quit: Callable[[], None] | None = None,
    ):
        self._on_show = on_show
        self._on_quit = on_quit
        self._tray = None

    def start(self):
        """Create and show the system tray icon."""
        try:
            from PySide6.QtWidgets import QSystemTrayIcon, QApplication, QMenu
            from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
            from PySide6.QtCore import Qt
        except ImportError:
            logger.warning("PySide6 not installed, system tray unavailable")
            return

        # Create a simple icon programmatically
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor("#7aa2f7"))
        painter = QPainter(pixmap)
        painter.setPen(QColor("#1a1b26"))
        font = QFont("Arial", 16, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "L")
        painter.end()

        icon = QIcon(pixmap)

        self._tray = QSystemTrayIcon(icon)
        self._tray.setToolTip("LifeOS — Second Brain")

        # Context menu
        menu = QMenu()

        show_action = menu.addAction("Show LifeOS")
        show_action.triggered.connect(self._show_window)

        menu.addSeparator()

        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self._quit)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_activated)
        self._tray.show()

        logger.info("System tray icon shown")

    def _on_activated(self, reason):
        from PySide6.QtWidgets import QSystemTrayIcon
        if reason == QSystemTrayIcon.DoubleClick:
            self._show_window()

    def _show_window(self):
        if self._on_show:
            self._on_show()

    def _quit(self):
        if self._on_quit:
            self._on_quit()
        self.hide()

    def hide(self):
        if self._tray:
            self._tray.hide()

    def show_message(self, title: str, message: str):
        if self._tray:
            self._tray.showMessage(title, message)

    @property
    def is_available(self) -> bool:
        try:
            from PySide6.QtWidgets import QSystemTrayIcon
            return QSystemTrayIcon.isSystemTrayAvailable()
        except ImportError:
            return False
