from __future__ import annotations

import time
import threading
from pathlib import Path
from typing import Callable

from app.privacy.exclusions import should_skip_dir, should_skip_file
from app.privacy.secrets import is_secret_file

import logging

logger = logging.getLogger(__name__)


class FileWatcher:
    """Watches a directory for file changes and triggers callbacks."""

    def __init__(
        self,
        root: Path,
        on_change: Callable[[Path, str], None] | None = None,
        debounce_seconds: float = 2.0,
    ):
        self._root = root
        self._on_change = on_change
        self._debounce = debounce_seconds
        self._observer = None
        self._running = False
        self._pending: dict[str, float] = {}
        self._lock = threading.Lock()

    def start(self):
        """Start watching the directory."""
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            logger.error("watchdog not installed. Run: pip install watchdog")
            return

        watcher = self

        class Handler(FileSystemEventHandler):
            def on_any_event(self, event):
                if event.is_directory:
                    return

                path = Path(event.src_path)

                # Skip excluded dirs/files
                try:
                    rel = path.relative_to(watcher._root)
                    parts = rel.parts
                    if parts and should_skip_dir(parts[0]):
                        return
                    if should_skip_file(path.name):
                        return
                    if is_secret_file(path):
                        return
                except ValueError:
                    return

                # Determine event type
                if event.event_type in ("created", "modified"):
                    event_type = "modified"
                elif event.event_type == "deleted":
                    event_type = "deleted"
                elif event.event_type == "moved":
                    event_type = "modified"
                else:
                    return

                # Debounce
                key = str(path)
                with watcher._lock:
                    watcher._pending[key] = (time.time(), event_type)

                logger.debug("File %s: %s", event_type, path.name)

        self._observer = Observer()
        handler = Handler()
        self._observer.schedule(handler, str(self._root), recursive=True)
        self._observer.start()
        self._running = True

        # Start debounce processor
        self._processor_thread = threading.Thread(
            target=self._process_pending, daemon=True
        )
        self._processor_thread.start()

        logger.info("File watcher started on %s", self._root)

    def _process_pending(self):
        """Process pending changes after debounce period."""
        while self._running:
            time.sleep(0.5)

            now = time.time()
            ready: list[tuple[str, str]] = []

            with self._lock:
                for key, (timestamp, event_type) in list(self._pending.items()):
                    if now - timestamp >= self._debounce:
                        ready.append((key, event_type))
                        del self._pending[key]

            for key, event_type in ready:
                path = Path(key)
                if path.exists() and event_type == "modified":
                    if self._on_change:
                        try:
                            self._on_change(path, event_type)
                        except Exception as e:
                            logger.error("Callback error for %s: %s", path, e)
                elif not path.exists() and event_type == "deleted":
                    if self._on_change:
                        try:
                            self._on_change(path, event_type)
                        except Exception as e:
                            logger.error("Callback error for %s: %s", path, e)

    def stop(self):
        """Stop watching."""
        self._running = False
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
        logger.info("File watcher stopped")

    @property
    def is_running(self) -> bool:
        return self._running
