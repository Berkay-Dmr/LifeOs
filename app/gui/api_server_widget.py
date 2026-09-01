from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QLineEdit, QTextBrowser,
    QGroupBox,
)
from PySide6.QtCore import Qt

import logging

logger = logging.getLogger(__name__)


class APIServerWidget(QWidget):
    """API server control widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._server = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Title
        title = QLabel("API Server")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        # Server config
        config_group = QGroupBox("Server Configuration")
        config_layout = QHBoxLayout(config_group)

        config_layout.addWidget(QLabel("Host:"))
        self.host_input = QLineEdit("0.0.0.0")
        self.host_input.setMaximumWidth(150)
        config_layout.addWidget(self.host_input)

        config_layout.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit("8000")
        self.port_input.setMaximumWidth(100)
        config_layout.addWidget(self.port_input)

        config_layout.addStretch()

        self.start_btn = QPushButton("Start Server")
        self.start_btn.clicked.connect(self._start_server)
        config_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop Server")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_server)
        config_layout.addWidget(self.stop_btn)

        layout.addWidget(config_group)

        # Status
        self.status_label = QLabel("Status: Stopped")
        self.status_label.setStyleSheet("color: #8b949e; font-size: 13px;")
        layout.addWidget(self.status_label)

        # Endpoints info
        endpoints_group = QGroupBox("Available Endpoints")
        endpoints_layout = QVBoxLayout(endpoints_group)

        self.endpoints_text = QTextBrowser()
        self.endpoints_text.setMaximumHeight(200)
        self.endpoints_text.setStyleSheet("background: transparent; border: none;")
        self.endpoints_text.setHtml(self._get_endpoints_html())
        endpoints_layout.addWidget(self.endpoints_text)

        layout.addWidget(endpoints_group)

        # Log
        log_group = QGroupBox("Server Log")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextBrowser()
        self.log_text.setStyleSheet("background: rgba(22,27,34,0.8); border: 1px solid #30363d; border-radius: 8px; padding: 8px;")
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

    def _get_endpoints_html(self) -> str:
        return """
        <b>GET</b> /api/health - Health check<br>
        <b>GET</b> /api/search?query=... - Search across all data<br>
        <b>GET</b> /api/stats - Knowledge base statistics<br>
        <b>GET</b> /api/graph - Graph data<br>
        <b>GET</b> /api/memory - List memories<br>
        <b>GET</b> /api/decisions - List decisions<br>
        <b>GET</b> /api/bugs - List bugs<br>
        <b>POST</b> /api/ask - Ask AI question<br>
        <b>POST</b> /api/memory - Create memory<br>
        <b>POST</b> /api/decisions - Create decision<br>
        <b>POST</b> /api/bugs - Create bug<br>
        """

    def _start_server(self):
        try:
            from app.api.server import LifeOSServer

            host = self.host_input.text().strip()
            port = int(self.port_input.text().strip())

            self._server = LifeOSServer(host=host, port=port)
            self._server.start()

            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText(f"Status: Running on http://{host}:{port}")
            self.status_label.setStyleSheet("color: #3fb950; font-size: 13px; font-weight: bold;")

            self._log(f"Server started on {host}:{port}")

        except Exception as e:
            self._log(f"Failed to start: {e}")
            logger.error("API server start failed: %s", e)

    def _stop_server(self):
        if self._server:
            self._server.stop()
            self._server = None

            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText("Status: Stopped")
            self.status_label.setStyleSheet("color: #8b949e; font-size: 13px;")

            self._log("Server stopped")

    def _log(self, message: str):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def closeEvent(self, event):
        if self._server:
            self._server.stop()
        event.accept()
