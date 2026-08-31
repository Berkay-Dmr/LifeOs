from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QLineEdit, QPushButton, QComboBox,
    QFileDialog, QMessageBox, QTabWidget,
)
from PySide6.QtCore import Qt

import logging

logger = logging.getLogger(__name__)


class SettingsWidget(QWidget):
    """Settings page with multi-provider support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("Settings")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        subtitle = QLabel("Configure LifeOS — AI Provider, Root Directory, Models")
        subtitle.setObjectName("subtitleLabel")
        layout.addWidget(subtitle)

        # Settings card
        card = QFrame()
        card.setObjectName("resultCard")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)

        # Root directory
        root_label = QLabel("Root Directory")
        root_label.setStyleSheet("font-weight: bold;")
        card_layout.addWidget(root_label)

        root_layout = QHBoxLayout()
        self.root_input = QLineEdit()
        self.root_input.setReadOnly(True)
        root_layout.addWidget(self.root_input)

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_root)
        root_layout.addWidget(browse_btn)

        card_layout.addLayout(root_layout)

        # AI Provider selection
        provider_label = QLabel("AI Provider")
        provider_label.setStyleSheet("font-weight: bold;")
        card_layout.addWidget(provider_label)

        provider_layout = QHBoxLayout()
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["auto", "openai", "gemini"])
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_layout.addWidget(self.provider_combo)
        provider_layout.addStretch()
        card_layout.addLayout(provider_layout)

        # OpenAI settings
        self.openai_frame = QFrame()
        openai_layout = QVBoxLayout(self.openai_frame)
        openai_layout.setContentsMargins(0, 0, 0, 0)

        openai_key_label = QLabel("OpenAI API Key")
        openai_key_label.setStyleSheet("font-weight: bold;")
        openai_layout.addWidget(openai_key_label)

        openai_key_layout = QHBoxLayout()
        self.openai_key_input = QLineEdit()
        self.openai_key_input.setEchoMode(QLineEdit.Password)
        self.openai_key_input.setPlaceholderText("sk-...")
        openai_key_layout.addWidget(self.openai_key_input)

        toggle_btn = QPushButton("Show")
        toggle_btn.setFixedWidth(60)
        toggle_btn.clicked.connect(lambda: self._toggle_visibility(self.openai_key_input))
        openai_key_layout.addWidget(toggle_btn)
        openai_layout.addLayout(openai_key_layout)

        openai_model_label = QLabel("OpenAI Model")
        openai_layout.addWidget(openai_model_label)

        self.openai_model_combo = QComboBox()
        self.openai_model_combo.addItems([
            "gpt-4o", "gpt-4o-mini", "gpt-4o-2024-11-20",
            "gpt-4-turbo", "gpt-4",
            "gpt-3.5-turbo", "gpt-3.5-turbo-16k",
            "o1", "o1-mini", "o3", "o3-mini",
        ])
        openai_layout.addWidget(self.openai_model_combo)

        card_layout.addWidget(self.openai_frame)

        # Gemini settings
        self.gemini_frame = QFrame()
        gemini_layout = QVBoxLayout(self.gemini_frame)
        gemini_layout.setContentsMargins(0, 0, 0, 0)

        gemini_key_label = QLabel("Gemini API Key")
        gemini_key_label.setStyleSheet("font-weight: bold;")
        gemini_layout.addWidget(gemini_key_label)

        gemini_key_layout = QHBoxLayout()
        self.gemini_key_input = QLineEdit()
        self.gemini_key_input.setEchoMode(QLineEdit.Password)
        self.gemini_key_input.setPlaceholderText("AIza...")
        gemini_key_layout.addWidget(self.gemini_key_input)

        toggle_btn2 = QPushButton("Show")
        toggle_btn2.setFixedWidth(60)
        toggle_btn2.clicked.connect(lambda: self._toggle_visibility(self.gemini_key_input))
        gemini_key_layout.addWidget(toggle_btn2)
        gemini_layout.addLayout(gemini_key_layout)

        gemini_model_label = QLabel("Gemini Model")
        gemini_layout.addWidget(gemini_model_label)

        self.gemini_model_combo = QComboBox()
        self.gemini_model_combo.addItems([
            "gemini-2.5-flash", "gemini-2.5-pro",
            "gemini-2.0-flash", "gemini-2.0-flash-lite",
            "gemini-1.5-pro", "gemini-1.5-flash",
        ])
        gemini_layout.addWidget(self.gemini_model_combo)

        card_layout.addWidget(self.gemini_frame)

        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save)
        card_layout.addWidget(save_btn)

        card_layout.addStretch()
        layout.addWidget(card)

        # Status
        self.status_label = QLabel("")
        self.status_label.setObjectName("subtitleLabel")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Load current settings
        self._load_settings()
        self._on_provider_changed(self.provider_combo.currentText())

    def _on_provider_changed(self, provider: str):
        self.openai_frame.setVisible(provider in ("auto", "openai"))
        self.gemini_frame.setVisible(provider in ("auto", "gemini"))

    def _load_settings(self):
        try:
            from app.config.settings import get_settings
            settings = get_settings()
            self.root_input.setText(str(settings.root_directory or ""))
            self.openai_key_input.setText(settings.openai_api_key or "")
            self.gemini_key_input.setText(settings.gemini_api_key or "")

            # Set provider
            idx = self.provider_combo.findText(settings.ai_provider)
            if idx >= 0:
                self.provider_combo.setCurrentIndex(idx)

            # Set models
            idx = self.openai_model_combo.findText(settings.openai_model)
            if idx >= 0:
                self.openai_model_combo.setCurrentIndex(idx)

            idx = self.gemini_model_combo.findText(settings.gemini_model)
            if idx >= 0:
                self.gemini_model_combo.setCurrentIndex(idx)

        except Exception as e:
            logger.error("Load settings failed: %s", e)

    def _browse_root(self):
        path = QFileDialog.getExistingDirectory(self, "Select Root Directory")
        if path:
            self.root_input.setText(path)

    def _toggle_visibility(self, input_field: QLineEdit):
        if input_field.echoMode() == QLineEdit.Password:
            input_field.setEchoMode(QLineEdit.Normal)
        else:
            input_field.setEchoMode(QLineEdit.Password)

    def _save(self):
        try:
            import os
            env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

            root = self.root_input.text().strip()
            provider = self.provider_combo.currentText()
            openai_key = self.openai_key_input.text().strip()
            openai_model = self.openai_model_combo.currentText()
            gemini_key = self.gemini_key_input.text().strip()
            gemini_model = self.gemini_model_combo.currentText()

            lines = []
            if root:
                lines.append(f"LIFEOS_ROOT_DIRECTORY={root}")
            lines.append(f"LIFEOS_AI_PROVIDER={provider}")
            if openai_key:
                lines.append(f"OPENAI_API_KEY={openai_key}")
            lines.append(f"OPENAI_MODEL={openai_model}")
            if gemini_key:
                lines.append(f"GEMINI_API_KEY={gemini_key}")
            lines.append(f"GEMINI_MODEL={gemini_model}")

            with open(env_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")

            self.status_label.setText("Settings saved successfully!")
            self.status_label.setStyleSheet("color: #9ece6a;")

        except Exception as e:
            logger.error("Save settings failed: %s", e)
            self.status_label.setText(f"Error: {e}")
            self.status_label.setStyleSheet("color: #f7768e;")
