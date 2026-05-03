"""
Storyteller Backend Configuration

1. Secrets: Loaded from .env file (API keys, connection strings)
2. Configuration: specified in this file
"""

from pydantic_settings import BaseSettings
from typing import Optional, List, Literal
from pathlib import Path
from enum import StrEnum
from dataclasses import dataclass


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
# PROVIDER PROFILES
# ============================================

class Provider(StrEnum):
    GEMINI = "gemini"
    OPENAI = "openai"


@dataclass(frozen=True)
class ProviderProfile:
    """All per-provider settings bundled in one place.

    Adding a new provider = add one entry to PROVIDER_PROFILES below.
    """
    chat_model: str
    embedding_model: str
    image_model: str
    image_size: str
    chat_rpm: int
    embedding_rpm: int
    langchain_chat_provider: str       # provider key for langchain.init_chat_model
    langchain_embeddings_provider: str  # provider key for langchain embeddings
    image_quality: Optional[str] = None  # OpenAI-only
    # 0 disables Gemini's internal reasoning so output tokens aren't consumed by it.
    # None = use SDK default (applicable to providers without thinking).
    thinking_budget: Optional[int] = None


PROVIDER_PROFILES: dict[Provider, ProviderProfile] = {
    Provider.GEMINI: ProviderProfile(
        chat_model="gemini-2.5-flash-lite",  # temp: higher free-tier RPD; revert to gemini-2.5-flash when billing enabled
        embedding_model="gemini-embedding-001",
        image_model="gemini-2.5-flash-image",
        image_size="1K",
        chat_rpm=5,        # Free tier: 5 requests/min
        embedding_rpm=20,  # Conservative: avoids 429s on free tier
        langchain_chat_provider="google_genai",
        langchain_embeddings_provider="google_genai",
        thinking_budget=0,  # gemini-2.5-flash thinking eats output budget; disable
    ),
    Provider.OPENAI: ProviderProfile(
        chat_model="gpt-4o-mini",
        embedding_model="text-embedding-3-small",
        image_model="dall-e-2",
        image_size="256x256",
        chat_rpm=0,        # 0 = no throttle
        embedding_rpm=0,   # 0 = no throttle
        langchain_chat_provider="openai",
        langchain_embeddings_provider="openai",
        image_quality="standard",
    ),
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

    # Active provider — toggle here to switch between Gemini / OpenAI
    provider: Provider = Provider.GEMINI

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

    @property
    def _profile(self) -> ProviderProfile:
        return PROVIDER_PROFILES[self._config.provider]

    def __validate_api_key(self):
        """Raise ValueError if the active provider's API key is missing."""
        provider = self._config.provider
        if provider is Provider.GEMINI and not self._secrets.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is required when provider is 'gemini'. "
                "Set it in your .env file."
            )
        if provider is Provider.OPENAI and not self._secrets.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when provider is 'openai'. "
                "Set it in your .env file."
            )

    # ============================================
    # Provider resolution
    # ============================================
    @property
    def provider(self) -> Provider:
        return self._config.provider

    @property
    def langchain_chat_provider(self) -> str:
        return self._profile.langchain_chat_provider

    @property
    def langchain_embeddings_provider(self) -> str:
        return self._profile.langchain_embeddings_provider

    # ============================================
    # Model resolution (delegated to active profile)
    # ============================================
    @property
    def chat_model(self) -> str:
        return self._profile.chat_model

    @property
    def embedding_model(self) -> str:
        return self._profile.embedding_model

    @property
    def image_model(self) -> str:
        return self._profile.image_model

    @property
    def image_size(self) -> str:
        return self._profile.image_size

    @property
    def image_quality(self) -> Optional[str]:
        return self._profile.image_quality

    @property
    def chat_rpm(self) -> int:
        return self._profile.chat_rpm

    @property
    def embedding_rpm(self) -> int:
        return self._profile.embedding_rpm

    @property
    def thinking_budget(self) -> Optional[int]:
        return self._profile.thinking_budget

    # ============================================
    # API Keys
    # ============================================
    @property
    def api_key(self) -> str:
        """Return the active provider's API key."""
        if self._config.provider is Provider.GEMINI:
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
