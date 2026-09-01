from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


class LifeOSSettings:
    """Settings class without pydantic dependency."""

    def __init__(self):
        # Load .env file manually
        self._load_env()

        # Paths
        self.root_directory: Optional[str] = os.getenv("LIFEOS_ROOT_DIRECTORY") or os.getenv("LIFEOS_ROOT")
        self.data_dir: str = os.getenv("LIFEOS_DATA_DIR", "data")
        self.log_level: str = os.getenv("LIFEOS_LOG_LEVEL", "INFO")

        # Indexing
        self.max_file_size_mb: int = int(os.getenv("LIFEOS_MAX_FILE_SIZE_MB", "50"))

        # Chunking
        self.chunk_size: int = int(os.getenv("LIFEOS_CHUNK_SIZE", "800"))
        self.chunk_overlap: int = int(os.getenv("LIFEOS_CHUNK_OVERLAP", "100"))

        # Search
        self.search_top_k: int = int(os.getenv("LIFEOS_SEARCH_TOP_K", "10"))
        self.semantic_weight: float = float(os.getenv("LIFEOS_SEMANTIC_WEIGHT", "0.55"))
        self.keyword_weight: float = float(os.getenv("LIFEOS_KEYWORD_WEIGHT", "0.25"))
        self.recency_weight: float = float(os.getenv("LIFEOS_RECENCY_WEIGHT", "0.10"))
        self.metadata_weight: float = float(os.getenv("LIFEOS_METADATA_WEIGHT", "0.10"))

        # Embedding
        self.embedding_model: str = os.getenv("LIFEOS_EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")

        # AI - read from env directly (no prefix for API keys)
        self.ai_provider: str = os.getenv("LIFEOS_AI_PROVIDER", "auto")
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.max_context_chunks: int = int(os.getenv("LIFEOS_MAX_CONTEXT_CHUNKS", "8"))

        # Privacy
        self.redact_secrets: bool = os.getenv("LIFEOS_REDACT_SECRETS", "true").lower() == "true"
        self.local_only: bool = os.getenv("LIFEOS_LOCAL_ONLY", "false").lower() == "true"

    def _load_env(self):
        """Load .env file manually."""
        env_paths = [Path(".env"), Path.home() / ".lifeos" / ".env"]
        for env_path in env_paths:
            if env_path.exists():
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, _, value = line.partition("=")
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key and key not in os.environ:
                                os.environ[key] = value
                break

    @property
    def root_path(self) -> Optional[Path]:
        if self.root_directory:
            return Path(self.root_directory)
        return None

    @property
    def data_path(self) -> Path:
        root = self.root_path or Path(".")
        return root / self.data_dir

    @property
    def db_path(self) -> Path:
        return self.data_path / "lifeos.db"

    @property
    def vectors_path(self) -> Path:
        """FAISS-safe path: use ~/.lifeos/vectors if root has non-ASCII chars."""
        import hashlib
        data = self.data_path

        # Check if path has non-ASCII characters (FAISS can't handle them)
        try:
            str(data).encode("ascii")
            return data / "vectors"
        except UnicodeEncodeError:
            # Fallback to ~/.lifeos/vectors/<hash>
            home = Path.home() / ".lifeos" / "vectors"
            root_hash = hashlib.md5(str(data).encode()).hexdigest()[:8]
            return home / root_hash


def get_settings() -> LifeOSSettings:
    return LifeOSSettings()
