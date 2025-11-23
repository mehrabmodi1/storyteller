"""
Storyteller Backend Configuration

Centralized configuration management using Pydantic Settings.
All settings can be overridden via environment variables or .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List, Literal
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    
    All settings have sensible defaults except for required API keys.
    """
    
    # ============================================
    # API Server Configuration
    # ============================================
    api_host: str = Field(
        default="0.0.0.0",
        description="Host to bind the API server to"
    )
    api_port: int = Field(
        default=8000,
        description="Port to run the API server on"
    )
    api_reload: bool = Field(
        default=True,
        description="Enable auto-reload in development"
    )
    
    # ============================================
    # OpenAI Configuration (REQUIRED)
    # ============================================
    openai_api_key: str = Field(
        ...,
        description="OpenAI API key (required)"
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model for vector search"
    )
    chat_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI chat model for story generation"
    )
    image_model: str = Field(
        default="dall-e-2",
        description="OpenAI image generation model"
    )
    image_generation_size: str = Field(
        default="1024x1024",
        description="Size of generated images (1024x1024, 1792x1024, 1024x1792)"
    )
    image_generation_quality: str = Field(
        default="standard",
        description="Image quality (standard or hd)"
    )
    
    # ============================================
    # Azure Storage (Optional - for image hosting)
    # ============================================
    azure_storage_connection_string: Optional[str] = Field(
        default=None,
        description="Azure Storage connection string for image hosting"
    )
    azure_container_name: Optional[str] = Field(
        default=None,
        description="Azure Storage container name"
    )
    
    # ============================================
    # Data Paths (relative to project root)
    # ============================================
    data_dir: str = Field(
        default="../data",
        description="Path to data directory (vector DBs, indexes)"
    )
    saved_graphs_dir: str = Field(
        default="../saved_graphs",
        description="Path to saved user journeys"
    )
    personas_file: str = Field(
        default="config/personas.json",
        description="Path to personas configuration file"
    )
    
    # ============================================
    # CORS Configuration
    # ============================================
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="List of allowed CORS origins"
    )
    
    # ============================================
    # Retrieval Configuration
    # ============================================
    retrieval_top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of chunks to retrieve from corpus"
    )
    bm25_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Weight for BM25 keyword search (0-1)"
    )
    semantic_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Weight for semantic vector search (0-1)"
    )
    
    # ============================================
    # Story Generation Configuration
    # ============================================
    default_story_length: int = Field(
        default=1500,
        ge=500,
        le=3000,
        description="Default story length in tokens"
    )
    min_story_length: int = Field(
        default=500,
        description="Minimum allowed story length"
    )
    max_story_length: int = Field(
        default=3000,
        description="Maximum allowed story length"
    )
    
    # ============================================
    # Authentication Mode
    # ============================================
    auth_mode: Literal["self_hosted", "per_request_key", "credit_system"] = Field(
        default="self_hosted",
        description="Authentication mode for OpenAI API access"
    )
    
    # Optional: Platform key for credit_system mode (Phase 3+)
    platform_openai_key: Optional[str] = Field(
        default=None,
        description="Platform-managed OpenAI key for credit system mode"
    )
    
    # ============================================
    # Pydantic Settings Configuration
    # ============================================
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
    
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
    def uses_azure_storage(self) -> bool:
        """Check if Azure Storage is configured."""
        return (
            self.azure_storage_connection_string is not None
            and self.azure_container_name is not None
        )
    
    def validate_story_length(self, length: int) -> int:
        """Validate and clamp story length to allowed range."""
        return max(self.min_story_length, min(length, self.max_story_length))


# Global settings instance
# Import this in other modules: from config.settings import settings
settings = Settings()

