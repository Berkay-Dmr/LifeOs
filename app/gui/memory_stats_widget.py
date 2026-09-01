from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QGroupBox,
)
from PySide6.QtCore import Qt, QThread, Signal

import logging

logger = logging.getLogger(__name__)


class MemoryStatsWorker(QThread):
    """Worker thread for memory stats."""
    finished = Signal(dict)
    error = Signal(str)

    def run(self):
        try:
            from app.memory.advanced import get_memory_stats, get_important_memories, get_stale_memories
            stats = get_memory_stats()
            important = get_important_memories(limit=10)
            stale = get_stale_memories(days=30)
            self.finished.emit({"stats": stats, "important": important, "stale": stale})
        except Exception as e:
            self.error.emit(str(e))


class MemoryStatsWidget(QWidget):
    """Memory statistics and management widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Title
        title = QLabel("Memory Stats")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        # Stats cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self.stat_cards = {}
        for name, color in [("Total", "88,148,253"), ("Avg Score", "163,113,247"),
                            ("High", "63,185,80"), ("Low", "248,113,113"), ("Stale", "227,179,65")]:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: rgba({color},0.1);
                    border: 1px solid rgba({color},0.3);
                    border-radius: 8px;
                    padding: 12px;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(4)

            value = QLabel("0")
            value.setStyleSheet(f"font-size: 24px; font-weight: bold; color: rgb({color});")
            value.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(value)

            label = QLabel(name)
            label.setStyleSheet("color: #8b949e; font-size: 11px;")
            label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(label)

            self.stat_cards[name] = value
            stats_layout.addWidget(card)

        layout.addLayout(stats_layout)

        # Action buttons
        btn_layout = QHBoxLayout()

        self.decay_btn = QPushButton("Apply Temporal Decay")
        self.decay_btn.clicked.connect(self._apply_decay)
        btn_layout.addWidget(self.decay_btn)

        self.consolidate_btn = QPushButton("Consolidate Memories")
        self.consolidate_btn.clicked.connect(self._consolidate)
        btn_layout.addWidget(self.consolidate_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Important memories table
        important_group = QGroupBox("Important Memories")
        important_layout = QVBoxLayout(important_group)

        self.important_table = QTableWidget()
        self.important_table.setColumnCount(3)
        self.important_table.setHorizontalHeaderLabels(["Title", "Score", "Type"])
        self.important_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.important_table.setEditTriggers(QTableWidget.NoEditTriggers)
        important_layout.addWidget(self.important_table)

        layout.addWidget(important_group)

        # Stale memories table
        stale_group = QGroupBox("Stale Memories (>30 days)")
        stale_layout = QVBoxLayout(stale_group)

        self.stale_table = QTableWidget()
        self.stale_table.setColumnCount(3)
        self.stale_table.setHorizontalHeaderLabels(["Title", "Score", "Type"])
        self.stale_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.stale_table.setEditTriggers(QTableWidget.NoEditTriggers)
        stale_layout.addWidget(self.stale_table)

        layout.addWidget(stale_group)

    def _load_data(self):
        self.worker = MemoryStatsWorker()
        self.worker.finished.connect(self._on_data_loaded)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_data_loaded(self, data):
        stats = data["stats"]
        important = data["important"]
        stale = data["stale"]

        self.stat_cards["Total"].setText(str(stats.get("total_memories", 0)))
        self.stat_cards["Avg Score"].setText(f"{stats.get('avg_score', 0):.2f}")
        self.stat_cards["High"].setText(str(stats.get("high_importance", 0)))
        self.stat_cards["Low"].setText(str(stats.get("low_importance", 0)))
        self.stat_cards["Stale"].setText(str(stats.get("stale_memories", 0)))

        # Important table
        self.important_table.setRowCount(len(important))
        for i, m in enumerate(important):
            self.important_table.setItem(i, 0, QTableWidgetItem(m.get("title", "")[:60]))
            self.important_table.setItem(i, 1, QTableWidgetItem(f"{m.get('score', 0):.2f}"))
            self.important_table.setItem(i, 2, QTableWidgetItem(m.get("type", "")))

        # Stale table
        self.stale_table.setRowCount(len(stale))
        for i, m in enumerate(stale):
            self.stale_table.setItem(i, 0, QTableWidgetItem(m.get("title", "")[:60]))
            self.stale_table.setItem(i, 1, QTableWidgetItem(f"{m.get('score', 0):.2f}"))
            self.stale_table.setItem(i, 2, QTableWidgetItem(m.get("type", "")))

    def _on_error(self, error):
        logger.error("Memory stats error: %s", error)

    def _apply_decay(self):
        try:
            from app.memory.advanced import apply_temporal_decay
            affected = apply_temporal_decay()
            from app.gui.notifications import notifications
            notifications.info(f"Decay applied to {affected} records")
            self._load_data()
        except Exception as e:
            logger.error("Decay failed: %s", e)

    def _consolidate(self):
        try:
            from app.memory.advanced import consolidate_memories
            result = consolidate_memories()
            from app.gui.notifications import notifications
            notifications.info(f"Merged {result['merged']} duplicates")
            self._load_data()
        except Exception as e:
            logger.error("Consolidate failed: %s", e)
