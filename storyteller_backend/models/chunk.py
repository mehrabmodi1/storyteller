"""
Chunk data models for text processing and retrieval.

Migrated from src/schemas/schemas.py
"""

from pydantic import BaseModel, Field, computed_field
from typing import List, Optional
import hashlib


class DocumentPosition(BaseModel):
    """Defines the position of a chunk within the source document."""
    
    start_token_index: int = Field(..., description="Starting token index in document")
    end_token_index: int = Field(..., description="Ending token index in document")


class Chunk(BaseModel):
    """
    Represents a processed chunk of text, including its content, context,
    and embedding information.
    """
    
    base_text: str = Field(..., description="The actual text content of the chunk")
    document_position: DocumentPosition = Field(..., description="Position in source document")
    context: Optional[str] = Field(
        default=None,
        description="Additional context surrounding the chunk"
    )
    embedding: Optional[List[float]] = Field(
        default=None,
        description="Vector embedding of the chunk"
    )
    embedding_model: Optional[str] = Field(
        default=None,
        description="Name of the model used for embedding"
    )

    @computed_field
    @property
    def chunk_id(self) -> str:
        """Generates a unique ID for the chunk by hashing its base text."""
        return hashlib.sha256(self.base_text.encode('utf-8')).hexdigest()

