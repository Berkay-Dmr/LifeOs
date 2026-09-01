from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextBrowser, QSplitter,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

import logging

logger = logging.getLogger(__name__)


class StatCard(QFrame):
    """A stat card with icon and value."""

    def __init__(self, icon: str, title: str, value: str, color: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba({color},0.15), stop:1 rgba({color},0.05));
                border: 1px solid rgba({color},0.3);
                border-radius: 12px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px; background: transparent;")
        layout.addWidget(icon_label)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: bold;
            color: rgb({color});
            background: transparent;
        """)
        layout.addWidget(value_label)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #8b949e; font-size: 12px; background: transparent;")
        layout.addWidget(title_label)


class DashboardWidget(QWidget):
    """Dashboard widget showing activity summary."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Title
        title = QLabel("Dashboard")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        # Stats cards row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self.cards = {}
        card_data = [
            ("📄", "Files", "0", "88,148,253"),
            ("💻", "Commits", "0", "63,185,80"),
            ("🐛", "Bugs", "0", "248,113,113"),
            ("📝", "Decisions", "0", "227,179,65"),
            ("🧠", "Memory", "0", "163,113,247"),
            ("✅", "Tasks", "0", "139,148,158"),
        ]

        for icon, title_text, value, color in card_data:
            card = StatCard(icon, title_text, value, color)
            self.cards[title_text.lower()] = card
            stats_layout.addWidget(card)

        layout.addLayout(stats_layout)

        # Content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)

        # Recent activity table
        activity_frame = QFrame()
        activity_frame.setStyleSheet("""
            QFrame {
                background: rgba(22,27,34,0.8);
                border: 1px solid #30363d;
                border-radius: 12px;
                padding: 12px;
            }
        """)
        activity_layout = QVBoxLayout(activity_frame)

        activity_title = QLabel("Recent Activity")
        activity_title.setStyleSheet("font-weight: bold; color: #58a6ff; font-size: 14px;")
        activity_layout.addWidget(activity_title)

        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(3)
        self.activity_table.setHorizontalHeaderLabels(["Type", "Title", "Time"])
        self.activity_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.activity_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.activity_table.setSelectionBehavior(QTableWidget.SelectRows)
        activity_layout.addWidget(self.activity_table)

        content_layout.addWidget(activity_frame)

        # Briefing panel
        briefing_frame = QFrame()
        briefing_frame.setStyleSheet("""
            QFrame {
                background: rgba(22,27,34,0.8);
                border: 1px solid #30363d;
                border-radius: 12px;
                padding: 12px;
            }
        """)
        briefing_layout = QVBoxLayout(briefing_frame)

        briefing_title = QLabel("Daily Briefing")
        briefing_title.setStyleSheet("font-weight: bold; color: #a371f7; font-size: 14px;")
        briefing_layout.addWidget(briefing_title)

        self.briefing_text = QTextBrowser()
        self.briefing_text.setStyleSheet("""
            QTextBrowser {
                background: transparent;
                border: none;
                color: #e6edf3;
                font-size: 13px;
            }
        """)
        briefing_layout.addWidget(self.briefing_text)

        content_layout.addWidget(briefing_frame)

        layout.addLayout(content_layout)

    def _load_data(self):
        try:
            from app.gui.dashboard import (
                get_activity_summary, get_recent_activity,
                generate_daily_briefing
            )

            # Load stats
            week_stats = get_activity_summary(days=7)
            today_stats = get_activity_summary(days=1)

            self.cards["files"].findChild(QLabel).text()
            # Update card values (simplified - just update the value label)
            self._update_card("files", str(week_stats.get("files_changed", 0)))
            self._update_card("commits", str(week_stats.get("commits", 0)))
            self._update_card("bugs", str(week_stats.get("bugs_solved", 0)))
            self._update_card("decisions", str(week_stats.get("decisions_made", 0)))
            self._update_card("memory", str(week_stats.get("memories_created", 0)))
            self._update_card("tasks", str(week_stats.get("tasks_created", 0)))

            # Load recent activity
            activities = get_recent_activity(limit=15)
            self.activity_table.setRowCount(len(activities))
            for i, act in enumerate(activities):
                type_item = QTableWidgetItem(act["type"])
                title_item = QTableWidgetItem(act["title"])
                time_item = QTableWidgetItem(act.get("timestamp", "")[:16])
                self.activity_table.setItem(i, 0, type_item)
                self.activity_table.setItem(i, 1, title_item)
                self.activity_table.setItem(i, 2, time_item)

            # Load briefing
            briefing = generate_daily_briefing()
            self.briefing_text.setPlainText(briefing)

        except Exception as e:
            logger.error("Failed to load dashboard: %s", e)

    def _update_card(self, card_name: str, value: str):
        """Update a stat card's value."""
        if card_name in self.cards:
            card = self.cards[card_name]
            # Find the value label (second child)
            for child in card.findChildren(QLabel):
                if child.font().pointSize() == 28 or child.font().pixelSize() >= 28:
                    child.setText(value)
                    break
