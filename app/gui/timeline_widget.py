from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QSizePolicy, QSpinBox, QPushButton,
)
from PySide6.QtCore import Qt, QTimer

import logging

logger = logging.getLogger(__name__)


class TimelineEvent(QFrame):
    """Single timeline event card."""

    def __init__(self, date: str, title: str, event_type: str, parent=None):
        super().__init__(parent)
        self.setObjectName("resultCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 10, 16, 10)

        # Icon
        icon = "📄" if event_type == "document" else "💡"
        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(28, 28)
        icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_lbl)

        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)

        title_lbl = QLabel(title)
        title_lbl.setWordWrap(True)
        font = title_lbl.font()
        font.setBold(True)
        title_lbl.setFont(font)
        content_layout.addWidget(title_lbl)

        date_lbl = QLabel(date)
        date_lbl.setStyleSheet("color: #787c99; font-size: 11px;")
        content_layout.addWidget(date_lbl)

        layout.addLayout(content_layout)


class TimelineWidget(QWidget):
    """Timeline page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("Timeline")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        subtitle = QLabel("Recent activity across your knowledge base")
        subtitle.setObjectName("subtitleLabel")
        layout.addWidget(subtitle)

        # Controls
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(12)

        days_label = QLabel("Days:")
        ctrl_layout.addWidget(days_label)

        self.days_spin = QSpinBox()
        self.days_spin.setRange(1, 365)
        self.days_spin.setValue(30)
        self.days_spin.setFixedWidth(80)
        ctrl_layout.addWidget(self.days_spin)

        load_btn = QPushButton("Load")
        load_btn.setObjectName("primaryBtn")
        load_btn.clicked.connect(self._load_timeline)
        ctrl_layout.addWidget(load_btn)

        ctrl_layout.addStretch()
        layout.addLayout(ctrl_layout)

        # Count
        self.count_label = QLabel("")
        self.count_label.setObjectName("subtitleLabel")
        layout.addWidget(self.count_label)

        # Timeline list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.events_container = QWidget()
        self.events_layout = QVBoxLayout(self.events_container)
        self.events_layout.setContentsMargins(0, 0, 0, 0)
        self.events_layout.setSpacing(4)
        self.events_layout.addStretch()

        scroll.setWidget(self.events_container)
        layout.addWidget(scroll)

        # Load on show
        QTimer.singleShot(200, self._load_timeline)

    def _load_timeline(self):
        try:
            from app.memory.timeline import build_timeline

            days = self.days_spin.value()
            events = build_timeline(days=days)

            # Clear old
            while self.events_layout.count() > 1:
                item = self.events_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            self.count_label.setText(f"{len(events)} events in last {days} days")

            current_date = ""
            for event in events:
                if event.date != current_date:
                    current_date = event.date
                    date_header = QLabel(current_date)
                    date_header.setStyleSheet("font-weight: bold; color: #7aa2f7; padding: 8px 0 4px 0;")
                    self.events_layout.insertWidget(self.events_layout.count() - 1, date_header)

                card = TimelineEvent(
                    date=event.date,
                    title=event.title,
                    event_type=event.event_type,
                )
                self.events_layout.insertWidget(self.events_layout.count() - 1, card)

        except Exception as e:
            logger.error("Load timeline failed: %s", e)
            self.count_label.setText(f"Error: {e}")
