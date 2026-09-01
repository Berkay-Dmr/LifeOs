from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QComboBox, QSpinBox,
    QLineEdit, QProgressBar, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt, Signal, QThread

import logging

logger = logging.getLogger(__name__)


class BulkWorker(QThread):
    """Background worker for bulk operations."""
    progress = Signal(str)
    finished = Signal(int, str)  # count, message
    error = Signal(str)

    def __init__(self, operation: str, **kwargs):
        super().__init__()
        self.operation = operation
        self.kwargs = kwargs

    def run(self):
        try:
            from app.config.settings import get_settings
            from app.database.sqlite import init_db, get_connection
            from app.database.repositories import (
                delete_documents_by_extension,
                delete_documents_by_pattern,
                delete_old_documents,
                get_extension_stats,
            )

            settings = get_settings()
            init_db(settings.db_path)

            if self.operation == "delete_ext":
                ext = self.kwargs.get("ext", "")
                self.progress.emit(f"'{ext}' dosyalari siliniyor...")
                count = delete_documents_by_extension(ext)
                self.finished.emit(count, f"{count} dosya silindi ({ext})")

            elif self.operation == "delete_pattern":
                pattern = self.kwargs.get("pattern", "")
                self.progress.emit(f"'{pattern}' eslesen dosyalar siliniyor...")
                count = delete_documents_by_pattern(pattern)
                self.finished.emit(count, f"{count} dosya silindi ({pattern})")

            elif self.operation == "delete_old":
                days = self.kwargs.get("days", 30)
                self.progress.emit(f"{days} gun onceki dosyalar siliniyor...")
                count = delete_old_documents(days)
                self.finished.emit(count, f"{count} dosya silindi ({days} gun onceki)")

            elif self.operation == "reindex":
                from app.ingestion.scanner import scan_directory
                root = settings.root_path
                if not root:
                    self.error.emit("Root directory not set")
                    return
                self.progress.emit("Tum dosyalar yeniden indeksleniyor...")
                with get_connection() as conn:
                    conn.execute("DELETE FROM chunks")
                    conn.execute("DELETE FROM documents")
                stats = scan_directory(root, settings)
                self.finished.emit(stats.new, f"{stats.new} dosya indekslendi")

            elif self.operation == "stats":
                ext_stats = get_extension_stats()
                msg = "\n".join(f"{ext}: {cnt}" for ext, cnt in ext_stats.items())
                self.finished.emit(sum(ext_stats.values()), msg)

        except Exception as e:
            logger.error("Bulk operation failed: %s", e)
            self.error.emit(str(e))


class BulkOperationsWidget(QWidget):
    """Bulk operations management widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        title = QLabel("Toplu Islemler")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        # ── Extension stats ──────────────────────────────────────────────
        stats_frame = QFrame()
        stats_frame.setStyleSheet("QFrame { border: 1px solid #333; border-radius: 8px; padding: 12px; }")
        stats_layout = QVBoxLayout(stats_frame)

        stats_header = QLabel("Dosya Dagilimi")
        stats_header.setStyleSheet("font-weight: bold; color: #7aa2f7; font-size: 13px;")
        stats_layout.addWidget(stats_header)

        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Tur", "Adet"])
        self.stats_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.stats_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.stats_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.stats_table.setMaximumHeight(150)
        stats_layout.addWidget(self.stats_table)

        refresh_stats_btn = QPushButton("Yenile")
        refresh_stats_btn.clicked.connect(self._load_stats)
        stats_layout.addWidget(refresh_stats_btn)

        layout.addWidget(stats_frame)

        # ── Delete by extension ──────────────────────────────────────────
        delete_ext_frame = QFrame()
        delete_ext_frame.setStyleSheet("QFrame { border: 1px solid #333; border-radius: 8px; padding: 12px; }")
        delete_ext_layout = QHBoxLayout(delete_ext_frame)

        delete_ext_label = QLabel("Ture gore sil:")
        delete_ext_label.setStyleSheet("font-weight: bold;")
        delete_ext_layout.addWidget(delete_ext_label)

        self.ext_combo = QComboBox()
        self.ext_combo.setMinimumWidth(100)
        delete_ext_layout.addWidget(self.ext_combo)

        self.delete_ext_btn = QPushButton("Sil")
        self.delete_ext_btn.setStyleSheet("QPushButton { background: #f7768e; color: white; }")
        self.delete_ext_btn.clicked.connect(self._delete_by_extension)
        delete_ext_layout.addWidget(self.delete_ext_btn)

        delete_ext_layout.addStretch()
        layout.addWidget(delete_ext_frame)

        # ── Delete by pattern ────────────────────────────────────────────
        delete_pattern_frame = QFrame()
        delete_pattern_frame.setStyleSheet("QFrame { border: 1px solid #333; border-radius: 8px; padding: 12px; }")
        delete_pattern_layout = QHBoxLayout(delete_pattern_frame)

        delete_pattern_label = QLabel("Sablon ile sil:")
        delete_pattern_label.setStyleSheet("font-weight: bold;")
        delete_pattern_layout.addWidget(delete_pattern_label)

        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("Dosya adinda ara...")
        self.pattern_input.setMinimumWidth(200)
        delete_pattern_layout.addWidget(self.pattern_input)

        self.delete_pattern_btn = QPushButton("Sil")
        self.delete_pattern_btn.setStyleSheet("QPushButton { background: #f7768e; color: white; }")
        self.delete_pattern_btn.clicked.connect(self._delete_by_pattern)
        delete_pattern_layout.addWidget(self.delete_pattern_btn)

        delete_pattern_layout.addStretch()
        layout.addWidget(delete_pattern_frame)

        # ── Delete old files ─────────────────────────────────────────────
        delete_old_frame = QFrame()
        delete_old_frame.setStyleSheet("QFrame { border: 1px solid #333; border-radius: 8px; padding: 12px; }")
        delete_old_layout = QHBoxLayout(delete_old_frame)

        delete_old_label = QLabel("Eski dosyalari sil:")
        delete_old_label.setStyleSheet("font-weight: bold;")
        delete_old_layout.addWidget(delete_old_label)

        self.days_spin = QSpinBox()
        self.days_spin.setRange(1, 365)
        self.days_spin.setValue(90)
        self.days_spin.setSuffix(" gun")
        delete_old_layout.addWidget(self.days_spin)

        self.delete_old_btn = QPushButton("Sil")
        self.delete_old_btn.setStyleSheet("QPushButton { background: #f7768e; color: white; }")
        self.delete_old_btn.clicked.connect(self._delete_old)
        delete_old_layout.addWidget(self.delete_old_btn)

        delete_old_layout.addStretch()
        layout.addWidget(delete_old_frame)

        # ── Reindex all ──────────────────────────────────────────────────
        reindex_frame = QFrame()
        reindex_frame.setStyleSheet("QFrame { border: 1px solid #333; border-radius: 8px; padding: 12px; }")
        reindex_layout = QHBoxLayout(reindex_frame)

        reindex_label = QLabel("Tum dosyalari yeniden indeksle:")
        reindex_label.setStyleSheet("font-weight: bold;")
        reindex_layout.addWidget(reindex_label)

        reindex_layout.addStretch()

        self.reindex_btn = QPushButton("Yeniden Indeksle")
        self.reindex_btn.setStyleSheet("QPushButton { background: #ff9e64; color: #1a1b26; }")
        self.reindex_btn.clicked.connect(self._reindex_all)
        reindex_layout.addWidget(self.reindex_btn)

        layout.addWidget(reindex_frame)

        # ── Progress & status ────────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #787c99; font-size: 12px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Load initial stats
        self._load_stats()

    def _load_stats(self):
        try:
            from app.config.settings import get_settings
            from app.database.sqlite import init_db
            from app.database.repositories import get_extension_stats

            settings = get_settings()
            init_db(settings.db_path)
            ext_stats = get_extension_stats()

            self.stats_table.setRowCount(len(ext_stats))
            for i, (ext, cnt) in enumerate(ext_stats.items()):
                self.stats_table.setItem(i, 0, QTableWidgetItem(ext))
                self.stats_table.setItem(i, 1, QTableWidgetItem(str(cnt)))

            # Update combo box
            self.ext_combo.clear()
            for ext in ext_stats.keys():
                self.ext_combo.addItem(ext)

        except Exception as e:
            logger.error("Failed to load stats: %s", e)

    def _start_operation(self, operation: str, **kwargs):
        if self._worker and self._worker.isRunning():
            QMessageBox.warning(self, "Uyari", "Bir islem zaten devam ediyor.")
            return

        # Confirm
        reply = QMessageBox.question(
            self, "Onay",
            "Bu islem geri alinamaz. Devam etmek istediginize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.status_label.setText("Islem baslatildi...")

        self._worker = BulkWorker(operation, **kwargs)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, msg: str):
        self.status_label.setText(msg)

    def _on_finished(self, count: int, msg: str):
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Tamamlandi: {msg}")
        self._load_stats()

    def _on_error(self, error: str):
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Hata: {error}")
        QMessageBox.critical(self, "Hata", error)

    def _delete_by_extension(self):
        ext = self.ext_combo.currentText()
        if not ext:
            return
        self._start_operation("delete_ext", ext=ext)

    def _delete_by_pattern(self):
        pattern = self.pattern_input.text().strip()
        if not pattern:
            return
        self._start_operation("delete_pattern", pattern=pattern)

    def _delete_old(self):
        days = self.days_spin.value()
        self._start_operation("delete_old", days=days)

    def _reindex_all(self):
        self._start_operation("reindex")
