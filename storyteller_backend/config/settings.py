"""
Storyteller Backend Configuration

1. Secrets: Loaded from .env file (API keys, connection strings)
2. Configuration: specified in this file
"""

from pydantic_settings import BaseSettings
from typing import Optional, List, Literal
from pathlib import Path


# ============================================
# SECRETS (loaded from .env file)
# ============================================

BACKEND_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = BACKEND_ROOT / ".env"


class Secrets(BaseSettings):
    """
    Secrets that must be provided via .env file.
    These are the ONLY values loaded from environment variables.
    """

    # Provider API keys (at least one required, depending on provider)
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # OPTIONAL
    platform_openai_key: Optional[str] = None  # For credit_system mode (Phase 3+)

    model_config = {
        "env_file": str(ENV_FILE_PATH),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


# ============================================
# CONFIGURATION (hardcoded, not from .env)
# ============================================

class Config:
    """
    Application configuration with hardcoded defaults.
    These values are NOT loaded from environment variables.
    """

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    # Active provider
    provider: Literal["gemini", "openai"] = "gemini"

    # Gemini Models
    gemini_chat_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_image_model: str = "gemini-2.5-flash-image"
    gemini_image_size: str = "1K"
    gemini_chat_rpm: int = 5       # Free tier: 5 requests/min
    gemini_embedding_rpm: int = 20   # Conservative: avoids 429s on free tier

    # OpenAI Models
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_image_model: str = "dall-e-2"
    openai_image_size: str = "256x256"
    openai_image_quality: str = "standard"
    openai_chat_rpm: int = 0       # 0 = no throttle
    openai_embedding_rpm: int = 0  # 0 = no throttle

    # Data Paths (relative to storyteller_backend/)
    data_dir: str = "../data"
    saved_graphs_dir: str = "../saved_graphs"
    personas_file: str = "config/personas.json"

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Retrieval
    retrieval_top_k: int = 10
    bm25_weight: float = 0.5
    semantic_weight: float = 0.5

    # Story Generation
    default_paragraph_count: int = 4
    min_paragraph_count: int = 1
    max_paragraph_count: int = 8
    words_per_paragraph: int = 200        # Used in prompt instruction
    max_tokens_per_paragraph: int = 300   # Used for max_tokens ceiling

    # Authentication
    auth_mode: Literal["self_hosted", "per_request_key", "credit_system"] = "self_hosted"

    # Image Storage
    local_image_storage: bool = True
    image_storage_limit_mb: int = 100


# ============================================
# PROVIDER MAPPINGS
# ============================================

_LANGCHAIN_CHAT_PROVIDER = {
    "gemini": "google_genai",
    "openai": "openai",
}

_LANGCHAIN_EMBEDDINGS_PROVIDER = {
    "gemini": "google_genai",
    "openai": "openai",
}


# ============================================
# COMBINED SETTINGS
# ============================================

class Settings:
    """
    Combined settings object with both secrets and configuration.

    Usage:
        from config.settings import settings
        settings.api_key        # Active provider's key
        settings.chat_model     # Resolved for active provider
    """

    def __init__(self):
        self._secrets = Secrets()
        self._config = Config()
        self.__validate_api_key()

    def __validate_api_key(self):
        """Raise ValueError if the active provider's API key is missing."""
        provider = self._config.provider
        if provider == "gemini" and not self._secrets.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is required when provider is 'gemini'. "
                "Set it in your .env file."
            )
        if provider == "openai" and not self._secrets.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when provider is 'openai'. "
                "Set it in your .env file."
            )

    # ============================================
    # Provider resolution
    # ============================================
    @property
    def provider(self) -> str:
        return self._config.provider

    @property
    def langchain_chat_provider(self) -> str:
        return _LANGCHAIN_CHAT_PROVIDER[self._config.provider]

    @property
    def langchain_embeddings_provider(self) -> str:
        return _LANGCHAIN_EMBEDDINGS_PROVIDER[self._config.provider]

    # ============================================
    # Model resolution (based on active provider)
    # ============================================
    @property
    def chat_model(self) -> str:
        p = self._config.provider
        return self._config.gemini_chat_model if p == "gemini" else self._config.openai_chat_model

    @property
    def embedding_model(self) -> str:
        p = self._config.provider
        return self._config.gemini_embedding_model if p == "gemini" else self._config.openai_embedding_model

    @property
    def image_model(self) -> str:
        p = self._config.provider
        return self._config.gemini_image_model if p == "gemini" else self._config.openai_image_model

    @property
    def image_size(self) -> str:
        p = self._config.provider
        return self._config.gemini_image_size if p == "gemini" else self._config.openai_image_size

    @property
    def image_quality(self) -> str:
        return self._config.openai_image_quality

    @property
    def chat_rpm(self) -> int:
        p = self._config.provider
        return self._config.gemini_chat_rpm if p == "gemini" else self._config.openai_chat_rpm

    @property
    def embedding_rpm(self) -> int:
        p = self._config.provider
        return self._config.gemini_embedding_rpm if p == "gemini" else self._config.openai_embedding_rpm

    # ============================================
    # API Keys
    # ============================================
    @property
    def api_key(self) -> str:
        """Return the active provider's API key."""
        if self._config.provider == "gemini":
            return self._secrets.gemini_api_key
        return self._secrets.openai_api_key

    def resolve_api_key(self, override: Optional[str] = None) -> str:
        """
        Return an API key, defaulting to the active provider's configured key.
        Allows override for per-request credentials.
        """
        return override or self.api_key

    @property
    def openai_api_key(self) -> Optional[str]:
        """Direct access to OpenAI key (needed for moderation regardless of provider)."""
        return self._secrets.openai_api_key

    @property
    def platform_openai_key(self) -> Optional[str]:
        return self._secrets.platform_openai_key

    # ============================================
    # Configuration (hardcoded)
    # ============================================
    @property
    def api_host(self) -> str:
        return self._config.api_host

    @property
    def api_port(self) -> int:
        return self._config.api_port

    @property
    def api_reload(self) -> bool:
        return self._config.api_reload

    @property
    def data_dir(self) -> str:
        return self._config.data_dir

    @property
    def saved_graphs_dir(self) -> str:
        return self._config.saved_graphs_dir

    @property
    def personas_file(self) -> str:
        return self._config.personas_file

    @property
    def cors_origins(self) -> List[str]:
        return self._config.cors_origins

    @property
    def retrieval_top_k(self) -> int:
        return self._config.retrieval_top_k

    @property
    def bm25_weight(self) -> float:
        return self._config.bm25_weight

    @property
    def semantic_weight(self) -> float:
        return self._config.semantic_weight

    @property
    def default_paragraph_count(self) -> int:
        return self._config.default_paragraph_count

    @property
    def min_paragraph_count(self) -> int:
        return self._config.min_paragraph_count

    @property
    def max_paragraph_count(self) -> int:
        return self._config.max_paragraph_count

    @property
    def words_per_paragraph(self) -> int:
        return self._config.words_per_paragraph

    @property
    def max_tokens_per_paragraph(self) -> int:
        return self._config.max_tokens_per_paragraph

    @property
    def auth_mode(self) -> Literal["self_hosted", "per_request_key", "credit_system"]:
        return self._config.auth_mode

    @property
    def local_image_storage(self) -> bool:
        return self._config.local_image_storage

    @property
    def image_storage_limit_mb(self) -> int:
        return self._config.image_storage_limit_mb

    # ============================================
    # Computed Properties
    # ============================================
    @property
    def data_path(self) -> Path:
        """Get data directory as Path object."""
        return Path(self.data_dir).resolve()

    @property
    def saved_graphs_path(self) -> Path:
        """Get saved graphs directory as Path object."""
        return Path(self.saved_graphs_dir).resolve()

    @property
    def personas_path(self) -> Path:
        """Get personas file as Path object."""
        return Path(self.personas_file).resolve()

    @property
    def image_storage_path(self) -> Path:
        """Get image storage directory: saved_graphs/images/"""
        return self.saved_graphs_path / "images"


# Global settings instance
# Import this in other modules: from config.settings import settings
settings = Settings()
