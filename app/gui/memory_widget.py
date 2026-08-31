from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QLabel, QFrame, QPushButton, QScrollArea, QSizePolicy,
    QComboBox, QMessageBox,
)
from PySide6.QtCore import Qt, Signal, QTimer

import logging

logger = logging.getLogger(__name__)


class MemoryCard(QFrame):
    """Single memory card."""

    def __init__(self, mem_id: str, content: str, mem_type: str, confidence: float, parent=None):
        super().__init__(parent)
        self.setObjectName("resultCard")
        self.mem_id = mem_id
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(16, 12, 16, 12)

        # Header
        header = QHBoxLayout()
        header.setSpacing(12)

        type_label = QLabel(mem_type)
        type_label.setObjectName("sourceLabel")
        header.addWidget(type_label)

        conf_label = QLabel(f"{confidence:.0%}")
        conf_label.setObjectName("scoreLabel")
        header.addWidget(conf_label)

        header.addStretch()

        delete_btn = QPushButton("x")
        delete_btn.setFixedSize(24, 24)
        delete_btn.setStyleSheet("background: #f7768e; color: #1a1b26; border-radius: 12px; font-weight: bold;")
        delete_btn.clicked.connect(self._on_delete)
        header.addWidget(delete_btn)

        layout.addLayout(header)

        # Content
        content_lbl = QLabel(content)
        content_lbl.setWordWrap(True)
        layout.addWidget(content_lbl)

        # ID
        id_lbl = QLabel(mem_id)
        id_lbl.setStyleSheet("color: #787c99; font-size: 11px;")
        layout.addWidget(id_lbl)

    def _on_delete(self):
        reply = QMessageBox.question(
            None, "Forget Memory",
            f"Are you sure you want to forget this memory?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                from app.memory.memory_engine import MemoryEngine
                engine = MemoryEngine()
                engine.forget(self.mem_id)
                self.setParent(None)
                self.deleteLater()
            except Exception as e:
                logger.error("Delete failed: %s", e)


class MemoryWidget(QWidget):
    """Memory management page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("Memories")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        subtitle = QLabel("Manually manage your memories")
        subtitle.setObjectName("subtitleLabel")
        layout.addWidget(subtitle)

        # Add memory form
        add_frame = QFrame()
        add_frame.setObjectName("resultCard")
        add_layout = QVBoxLayout(add_frame)

        # Content input
        self.content_input = QLineEdit()
        self.content_input.setPlaceholderText("Memory content...")
        self.content_input.returnPressed.connect(self._on_add)
        add_layout.addWidget(self.content_input)

        # Type + confidence row
        type_layout = QHBoxLayout()
        type_layout.setSpacing(8)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["fact", "solution", "problem", "project", "note", "decision"])
        self.type_combo.setFixedWidth(120)
        type_layout.addWidget(self.type_combo)

        add_btn = QPushButton("Add Memory")
        add_btn.setObjectName("primaryBtn")
        add_btn.clicked.connect(self._on_add)
        type_layout.addWidget(add_btn)

        type_layout.addStretch()
        add_layout.addLayout(type_layout)

        layout.addWidget(add_frame)

        # Filter row
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)

        filter_label = QLabel("Filter:")
        filter_layout.addWidget(filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["all", "fact", "solution", "problem", "project", "note", "decision"])
        self.filter_combo.currentTextChanged.connect(self._on_filter)
        filter_layout.addWidget(self.filter_combo)

        filter_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_memories)
        filter_layout.addWidget(refresh_btn)

        layout.addLayout(filter_layout)

        # Count
        self.count_label = QLabel("")
        self.count_label.setObjectName("subtitleLabel")
        layout.addWidget(self.count_label)

        # Memories list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.memories_container = QWidget()
        self.memories_layout = QVBoxLayout(self.memories_container)
        self.memories_layout.setContentsMargins(0, 0, 0, 0)
        self.memories_layout.setSpacing(8)
        self.memories_layout.addStretch()

        scroll.setWidget(self.memories_container)
        layout.addWidget(scroll)

        # Load on show
        QTimer.singleShot(100, self._load_memories)

    def _on_add(self):
        content = self.content_input.text().strip()
        if not content:
            return

        try:
            from app.memory.memory_engine import MemoryEngine
            engine = MemoryEngine()
            mem_type = self.type_combo.currentText()
            engine.create_memory(content, memory_type=mem_type, confidence=1.0)
            self.content_input.clear()
            self._load_memories()
        except Exception as e:
            logger.error("Add memory failed: %s", e)

    def _on_filter(self, _text):
        self._load_memories()

    def _load_memories(self):
        try:
            from app.memory.memory_engine import MemoryEngine
            engine = MemoryEngine()
            memories = engine.list_all(active_only=True)

            type_filter = self.filter_combo.currentText()
            if type_filter != "all":
                memories = [m for m in memories if m.type == type_filter]

            # Clear old
            while self.memories_layout.count() > 1:
                item = self.memories_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            self.count_label.setText(f"{len(memories)} memories")

            for mem in memories:
                card = MemoryCard(
                    mem_id=mem.id,
                    content=mem.content,
                    mem_type=mem.type,
                    confidence=mem.confidence,
                )
                self.memories_layout.insertWidget(self.memories_layout.count() - 1, card)

        except Exception as e:
            logger.error("Load memories failed: %s", e)
            self.count_label.setText(f"Error: {e}")
