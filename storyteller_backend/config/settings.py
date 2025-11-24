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

class Secrets(BaseSettings):
    """
    Secrets that must be provided via .env file.
    These are the ONLY values loaded from environment variables.
    """
    
    # REQUIRED
    openai_api_key: str
    
    # OPTIONAL
    platform_openai_key: Optional[str] = None  # For credit_system mode (Phase 3+)
    
    model_config = {
        "env_file": ".env",
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
    
    # OpenAI Models
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"
    image_model: str = "dall-e-2"
    image_generation_size: str = "1024x1024"
    image_generation_quality: str = "standard"
    
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
    default_story_length: int = 1500
    min_story_length: int = 500
    max_story_length: int = 3000
    
    # Authentication
    auth_mode: Literal["self_hosted", "per_request_key", "credit_system"] = "self_hosted"


# ============================================
# COMBINED SETTINGS
# ============================================

class Settings:
    """
    Combined settings object with both secrets and configuration.
    
    Usage:
        from config.settings import settings
        settings.openai_api_key  # From .env
        settings.chat_model      # Hardcoded
    """
    
    def __init__(self):
        self._secrets = Secrets()
        self._config = Config()
    
    # ============================================
    # Secrets (from .env)
    # ============================================
    @property
    def openai_api_key(self) -> str:
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
    def embedding_model(self) -> str:
        return self._config.embedding_model
    
    @property
    def chat_model(self) -> str:
        return self._config.chat_model
    
    @property
    def image_model(self) -> str:
        return self._config.image_model
    
    @property
    def image_generation_size(self) -> str:
        return self._config.image_generation_size
    
    @property
    def image_generation_quality(self) -> str:
        return self._config.image_generation_quality
    
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
    def default_story_length(self) -> int:
        return self._config.default_story_length
    
    @property
    def min_story_length(self) -> int:
        return self._config.min_story_length
    
    @property
    def max_story_length(self) -> int:
        return self._config.max_story_length
    
    @property
    def auth_mode(self) -> Literal["self_hosted", "per_request_key", "credit_system"]:
        return self._config.auth_mode
    
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
    
    def validate_story_length(self, length: int) -> int:
        """Validate and clamp story length to allowed range."""
        return max(self.min_story_length, min(length, self.max_story_length))


# Global settings instance
# Import this in other modules: from config.settings import settings
settings = Settings()
