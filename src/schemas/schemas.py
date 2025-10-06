from pydantic import BaseModel, Field, computed_field
from typing import List, Optional
import hashlib

class DocumentPosition(BaseModel):
    """Defines the position of a chunk within the source document."""
    start_token_index: int
    end_token_index: int

class Chunk(BaseModel):
    """
    Represents a processed chunk of text, including its content, context,
    and embedding information.
    """
    base_text: str
    document_position: DocumentPosition
    
    context: Optional[str] = None
    embedding: Optional[List[float]] = None
    embedding_model: Optional[str] = None

    @computed_field
    @property
    def chunk_id(self) -> str:
        """Generates a unique ID for the chunk by hashing its base text."""
        return hashlib.sha256(self.base_text.encode('utf-8')).hexdigest() 