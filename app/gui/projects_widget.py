from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QTextEdit, QComboBox,
    QSplitter, QMessageBox,
)
from PySide6.QtCore import Qt, Signal

import logging

logger = logging.getLogger(__name__)


class ProjectsWidget(QWidget):
    """Projects management widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_projects()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("Projects")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        subtitle = QLabel("Organize your work by projects")
        subtitle.setObjectName("subtitleLabel")
        layout.addWidget(subtitle)

        # Action buttons
        btn_layout = QHBoxLayout()

        discover_btn = QPushButton("Discover Projects")
        discover_btn.setObjectName("primaryBtn")
        discover_btn.setCursor(Qt.PointingHandCursor)
        discover_btn.clicked.connect(self._discover_projects)
        btn_layout.addWidget(discover_btn)

        add_btn = QPushButton("+ Add Project")
        add_btn.setObjectName("successBtn")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._add_project)
        btn_layout.addWidget(add_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Projects table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "Language", "Framework", "Status", "Path"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_project_double_click)
        layout.addWidget(self.table)

        # Stats
        self.stats_label = QLabel("")
        self.stats_label.setObjectName("subtitleLabel")
        layout.addWidget(self.stats_label)

    def _load_projects(self):
        try:
            from app.projects.manager import list_projects
            projects = list_projects()

            self.table.setRowCount(len(projects))
            for i, p in enumerate(projects):
                self.table.setItem(i, 0, QTableWidgetItem(p.name))
                self.table.setItem(i, 1, QTableWidgetItem(p.language or "-"))
                self.table.setItem(i, 2, QTableWidgetItem(p.framework or "-"))
                self.table.setItem(i, 3, QTableWidgetItem(p.status))
                self.table.setItem(i, 4, QTableWidgetItem(p.path))

            self.stats_label.setText(f"{len(projects)} project(s)")

        except Exception as e:
            logger.error("Failed to load projects: %s", e)

    def _discover_projects(self):
        try:
            from app.config.settings import get_settings
            from app.projects.manager import discover_projects

            settings = get_settings()
            if not settings.root_path:
                QMessageBox.warning(self, "Warning", "Root directory not set.")
                return

            discovered = discover_projects(settings.root_path)
            self._load_projects()

            QMessageBox.information(
                self, "Discovery Complete",
                f"Found {len(discovered)} project(s)."
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _add_project(self):
        # Simple dialog
        from PySide6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Project")
        dialog.setMinimumWidth(400)

        form = QFormLayout(dialog)

        name_input = QLineEdit()
        path_input = QLineEdit()
        lang_input = QComboBox()
        lang_input.addItems(["", "python", "javascript", "typescript", "java", "csharp", "go", "rust"])
        framework_input = QLineEdit()

        form.addRow("Name:", name_input)
        form.addRow("Path:", path_input)
        form.addRow("Language:", lang_input)
        form.addRow("Framework:", framework_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        if dialog.exec():
            name = name_input.text().strip()
            path = path_input.text().strip()
            if name and path:
                from app.projects.manager import create_project
                create_project(
                    name=name,
                    path=path,
                    language=lang_input.currentText() or None,
                    framework=framework_input.text().strip() or None,
                )
                self._load_projects()

    def _on_project_double_click(self, index):
        row = index.row()
        name = self.table.item(row, 0).text()
        path = self.table.item(row, 4).text()
        QMessageBox.information(
            self, "Project Info",
            f"Name: {name}\nPath: {path}"
        )
