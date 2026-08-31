from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LifeOSSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="LIFEOS_",
        extra="ignore",
    )

    # Paths
    root_directory: Optional[str] = Field(
        default=None,
        description="Root directory to index. Set via 'lifeos init'.",
    )
    data_dir: str = Field(
        default="data",
        description="Directory for database, vectors, and cache.",
    )
    log_level: str = Field(default="INFO", description="Logging level.")

    # Indexing
    max_file_size_mb: int = Field(
        default=50, description="Max file size in MB to index."
    )

    # Chunking
    chunk_size: int = Field(
        default=800, description="Chunk size in tokens (approx)."
    )
    chunk_overlap: int = Field(
        default=100, description="Overlap between chunks in tokens."
    )

    # Search
    search_top_k: int = Field(default=10, description="Number of search results.")
    semantic_weight: float = Field(default=0.55)
    keyword_weight: float = Field(default=0.25)
    recency_weight: float = Field(default=0.10)
    metadata_weight: float = Field(default=0.10)

    # AI
    ai_provider: str = Field(default="auto", description="AI provider: auto, openai, gemini")
    openai_api_key: str = Field(default="", description="OpenAI API key.", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model.", alias="OPENAI_MODEL")
    gemini_api_key: str = Field(default="", description="Google Gemini API key.", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", description="Gemini model.", alias="GEMINI_MODEL")
    max_context_chunks: int = Field(default=8, description="Max chunks in AI context.")

    # Privacy
    redact_secrets: bool = Field(default=True)
    local_only: bool = Field(default=False)

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
