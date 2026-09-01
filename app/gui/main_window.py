from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QStatusBar,
    QSizePolicy, QFrame,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon

from app.gui.styles import DARK_THEME, LIGHT_THEME
from app.gui.theme import theme_manager
from app.gui.search_widget import SearchWidget
from app.gui.ask_widget import AskWidget
from app.gui.memory_widget import MemoryWidget
from app.gui.timeline_widget import TimelineWidget
from app.gui.settings_widget import SettingsWidget
from app.gui.notifications import notifications


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

        # Apply initial theme
        self._apply_theme(theme_manager.current)

        # Initialize notification manager
        notifications.set_parent(self)

        self._init_ui()

        # Listen for theme changes
        theme_manager.on_change(self._on_theme_change)

    def _apply_theme(self, theme: str):
        """Apply the given theme."""
        if theme == "dark":
            self.setStyleSheet(DARK_THEME)
        else:
            self.setStyleSheet(LIGHT_THEME)

    def _on_theme_change(self, theme: str):
        """Handle theme change."""
        self._apply_theme(theme)

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

        # Logo
        logo_frame = QFrame()
        logo_frame.setStyleSheet("""
            QFrame {
                background: rgba(56,139,253,0.12);
                border-radius: 14px;
                padding: 10px;
            }
        """)
        logo_inner = QVBoxLayout(logo_frame)
        logo_inner.setContentsMargins(8, 8, 8, 8)

        logo = QLabel("🧠 LifeOS")
        logo.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #58a6ff;
            background: transparent;
        """)
        logo.setAlignment(Qt.AlignCenter)
        logo_inner.addWidget(logo)

        subtitle = QLabel("Second Brain")
        subtitle.setStyleSheet("""
            font-size: 11px;
            color: #a371f7;
            background: transparent;
        """)
        subtitle.setAlignment(Qt.AlignCenter)
        logo_inner.addWidget(subtitle)

        sidebar_layout.addWidget(logo_frame)
        sidebar_layout.addSpacing(12)

        # Nav buttons
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

        # Theme toggle button
        self.theme_btn = SidebarButton("🌙 Dark", "")
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.clicked.connect(self._toggle_theme)
        sidebar_layout.addWidget(self.theme_btn)

        # Version
        version = QLabel("v0.3.0")
        version.setObjectName("subtitleLabel")
        version.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(version)

        main_layout.addWidget(sidebar)

        # ── Page Stack ─────────────────────────────────────────────────────
        self.stack = QStackedWidget()

        self.search_widget = SearchWidget()
        self.ask_widget = AskWidget()
        self.memory_widget = MemoryWidget()
        self.timeline_widget = TimelineWidget()

        self._graph_widget = None
        self._bulk_widget = None
        self._settings_widget = None

        self.stack.addWidget(self.search_widget)
        self.stack.addWidget(self.ask_widget)
        self.stack.addWidget(self.memory_widget)
        self.stack.addWidget(self.timeline_widget)
        self.stack.addWidget(QWidget())
        self.stack.addWidget(QWidget())
        self.stack.addWidget(QWidget())

        main_layout.addWidget(self.stack)

        # Status bar
        self.statusBar().showMessage("Ready")

        # Default page
        self._switch_page(0)

    def _toggle_theme(self):
        """Toggle between dark and light theme."""
        theme_manager.toggle()
        is_dark = theme_manager.is_dark
        self.theme_btn.setText("🌙 Dark" if is_dark else "☀️ Light")
        notifications.info(f"Theme changed to {'Dark' if is_dark else 'Light'}")

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
