from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QStatusBar,
    QSizePolicy, QFrame,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon

from app.gui.styles import DARK_THEME
from app.gui.search_widget import SearchWidget
from app.gui.ask_widget import AskWidget
from app.gui.memory_widget import MemoryWidget
from app.gui.timeline_widget import TimelineWidget
from app.gui.settings_widget import SettingsWidget


class MainWindow(QMainWindow):
    """Main LifeOS window with sidebar navigation."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LifeOS — Second Brain")
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)

        # Apply dark theme
        self.setStyleSheet(DARK_THEME)

        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 16, 8, 16)
        sidebar_layout.setSpacing(4)

        # Logo
        logo = QLabel("LifeOS")
        logo.setObjectName("titleLabel")
        logo.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(logo)

        sidebar_layout.addSpacing(16)

        # Nav buttons
        self._nav_buttons: list[QPushButton] = []

        pages = [
            ("Search", 0),
            ("Ask AI", 1),
            ("Memories", 2),
            ("Timeline", 3),
            ("Graph", 4),
            ("Settings", 5),
        ]

        for text, index in pages:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=index: self._switch_page(i))
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # Version
        version = QLabel("v0.2.0")
        version.setObjectName("subtitleLabel")
        version.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(version)

        main_layout.addWidget(sidebar)

        # Page stack
        self.stack = QStackedWidget()

        self.search_widget = SearchWidget()
        self.ask_widget = AskWidget()
        self.memory_widget = MemoryWidget()
        self.timeline_widget = TimelineWidget()

        # Lazy load graph widget
        self._graph_widget = None
        self._settings_widget = None

        self.stack.addWidget(self.search_widget)
        self.stack.addWidget(self.ask_widget)
        self.stack.addWidget(self.memory_widget)
        self.stack.addWidget(self.timeline_widget)
        self.stack.addWidget(QWidget())  # Placeholder for graph
        self.stack.addWidget(QWidget())  # Placeholder for settings

        main_layout.addWidget(self.stack)

        # Status bar
        self.statusBar().showMessage("Ready")

        # Default page
        self._switch_page(0)

    def _switch_page(self, index: int):
        # Lazy load graph widget
        if index == 4 and self._graph_widget is None:
            try:
                from app.graph.graph_widget import GraphWidget
                self._graph_widget = GraphWidget()
                self.stack.removeWidget(self.stack.widget(4))
                self.stack.insertWidget(4, self._graph_widget)
            except Exception as e:
                print(f"Failed to load graph widget: {e}")

        # Lazy load settings widget
        if index == 5 and self._settings_widget is None:
            self._settings_widget = SettingsWidget()
            self.stack.removeWidget(self.stack.widget(5))
            self.stack.insertWidget(5, self._settings_widget)

        self.stack.setCurrentIndex(index)

        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == index)

    def closeEvent(self, event):
        event.accept()
