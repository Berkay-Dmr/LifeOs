from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QStatusBar,
    QSizePolicy, QFrame, QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QIcon, QLinearGradient, QColor

from app.gui.styles import DARK_THEME
from app.gui.search_widget import SearchWidget
from app.gui.ask_widget import AskWidget
from app.gui.memory_widget import MemoryWidget
from app.gui.timeline_widget import TimelineWidget
from app.gui.settings_widget import SettingsWidget


class SidebarButton(QPushButton):
    """Custom sidebar button with icon support."""

    def __init__(self, text: str, icon_char: str = "", parent=None):
        super().__init__(parent)
        self.setText(f"  {icon_char}  {text}" if icon_char else text)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)


class MainWindow(QMainWindow):
    """Main LifeOS window with sidebar navigation."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LifeOS — Second Brain")
        self.setMinimumSize(900, 600)
        self.resize(1200, 750)

        # Apply dark theme
        self.setStyleSheet(DARK_THEME)

        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ────────────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 20, 12, 20)
        sidebar_layout.setSpacing(4)

        # Logo with glow effect
        logo_frame = QFrame()
        logo_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(122,162,247,0.2), stop:1 rgba(187,154,247,0.1));
                border-radius: 16px;
                padding: 12px;
            }
        """)
        logo_inner = QVBoxLayout(logo_frame)
        logo_inner.setContentsMargins(8, 8, 8, 8)

        logo = QLabel("🧠 LifeOS")
        logo.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #7aa2f7;
            background: transparent;
        """)
        logo.setAlignment(Qt.AlignCenter)
        logo_inner.addWidget(logo)

        subtitle = QLabel("Second Brain")
        subtitle.setStyleSheet("""
            font-size: 11px;
            color: #bb9af7;
            background: transparent;
        """)
        subtitle.setAlignment(Qt.AlignCenter)
        logo_inner.addWidget(subtitle)

        sidebar_layout.addWidget(logo_frame)
        sidebar_layout.addSpacing(16)

        # Nav buttons with icons
        self._nav_buttons: list[QPushButton] = []

        pages = [
            ("Search", "🔍", 0),
            ("Ask AI", "💬", 1),
            ("Memories", "🧠", 2),
            ("Timeline", "📅", 3),
            ("Graph", "🕸️", 4),
            ("Bulk", "📦", 5),
            ("Settings", "⚙️", 6),
        ]

        for text, icon, index in pages:
            btn = SidebarButton(text, icon)
            btn.clicked.connect(lambda checked, i=index: self._switch_page(i))
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # Version badge
        version_frame = QFrame()
        version_frame.setStyleSheet("""
            QFrame {
                background: rgba(122,162,247,0.1);
                border-radius: 8px;
                padding: 4px;
            }
        """)
        version_layout = QVBoxLayout(version_frame)
        version_layout.setContentsMargins(0, 4, 0, 4)

        version = QLabel("v0.2.0")
        version.setStyleSheet("color: #7aa2f7; font-size: 11px; background: transparent;")
        version.setAlignment(Qt.AlignCenter)
        version_layout.addWidget(version)

        sidebar_layout.addWidget(version_frame)

        main_layout.addWidget(sidebar)

        # ── Page Stack ─────────────────────────────────────────────────────
        self.stack = QStackedWidget()

        self.search_widget = SearchWidget()
        self.ask_widget = AskWidget()
        self.memory_widget = MemoryWidget()
        self.timeline_widget = TimelineWidget()

        # Lazy load placeholders
        self._graph_widget = None
        self._bulk_widget = None
        self._settings_widget = None

        self.stack.addWidget(self.search_widget)
        self.stack.addWidget(self.ask_widget)
        self.stack.addWidget(self.memory_widget)
        self.stack.addWidget(self.timeline_widget)
        self.stack.addWidget(QWidget())  # Graph placeholder
        self.stack.addWidget(QWidget())  # Bulk placeholder
        self.stack.addWidget(QWidget())  # Settings placeholder

        main_layout.addWidget(self.stack)

        # ── Status Bar ─────────────────────────────────────────────────────
        self.statusBar().showMessage("Ready")

        # Default page
        self._switch_page(0)

    def _switch_page(self, index: int):
        # Lazy load widgets
        if index == 4 and self._graph_widget is None:
            try:
                from app.graph.graph_widget import GraphWidget
                self._graph_widget = GraphWidget()
                self.stack.removeWidget(self.stack.widget(4))
                self.stack.insertWidget(4, self._graph_widget)
            except Exception as e:
                print(f"Failed to load graph widget: {e}")

        if index == 5 and self._bulk_widget is None:
            try:
                from app.gui.bulk_widget import BulkOperationsWidget
                self._bulk_widget = BulkOperationsWidget()
                self.stack.removeWidget(self.stack.widget(5))
                self.stack.insertWidget(5, self._bulk_widget)
            except Exception as e:
                print(f"Failed to load bulk widget: {e}")

        if index == 6 and self._settings_widget is None:
            self._settings_widget = SettingsWidget()
            self.stack.removeWidget(self.stack.widget(6))
            self.stack.insertWidget(6, self._settings_widget)

        self.stack.setCurrentIndex(index)

        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == index)

    def closeEvent(self, event):
        event.accept()
