from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from app.config.settings import get_settings


class ThemeManager:
    """Manages dark/light theme switching."""

    _instance = None
    _listeners: list[Callable] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._current_theme = "dark"
            cls._instance._load_theme()
        return cls._instance

    def _load_theme(self):
        """Load saved theme preference."""
        settings = get_settings()
        theme_file = settings.data_path / "theme.json"
        if theme_file.exists():
            try:
                data = json.loads(theme_file.read_text(encoding="utf-8"))
                self._current_theme = data.get("theme", "dark")
            except Exception:
                self._current_theme = "dark"

    def _save_theme(self):
        """Save theme preference."""
        settings = get_settings()
        theme_file = settings.data_path / "theme.json"
        theme_file.parent.mkdir(parents=True, exist_ok=True)
        theme_file.write_text(
            json.dumps({"theme": self._current_theme}),
            encoding="utf-8"
        )

    @property
    def current(self) -> str:
        return self._current_theme

    @property
    def is_dark(self) -> bool:
        return self._current_theme == "dark"

    def toggle(self):
        """Toggle between dark and light."""
        self._current_theme = "light" if self._current_theme == "dark" else "dark"
        self._save_theme()
        self._notify_listeners()

    def set_theme(self, theme: str):
        """Set theme explicitly."""
        if theme in ("dark", "light"):
            self._current_theme = theme
            self._save_theme()
            self._notify_listeners()

    def on_change(self, callback: Callable):
        """Register a callback for theme changes."""
        self._listeners.append(callback)

    def _notify_listeners(self):
        for cb in self._listeners:
            try:
                cb(self._current_theme)
            except Exception:
                pass


# Global instance
theme_manager = ThemeManager()
