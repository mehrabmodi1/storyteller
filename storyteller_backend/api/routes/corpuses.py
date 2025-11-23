"""
Corpuses API Routes

Endpoints for managing text corpuses:
- GET /api/corpuses - List all corpuses with status
- POST /api/corpuses - Trigger new corpus ingestion
- PUT /api/corpuses/{name} - Update corpus metadata
- DELETE /api/corpuses/{name} - Delete corpus
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import List
from pydantic import BaseModel, Field

from models.api_models import CorpusInfo
from embed_retrieve import get_registry

router = APIRouter()


class CorpusCreateRequest(BaseModel):
    """Request model for creating a new corpus."""
    name: str = Field(..., description="Internal corpus name (lowercase, no spaces)")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Corpus description")
    source_file: str = Field(..., description="Path to source file")
    file_type: str = Field(..., description="File type: 'pdf' or 'text'")


class CorpusUpdateRequest(BaseModel):
    """Request model for updating corpus metadata."""
    display_name: str | None = None
    description: str | None = None
    is_active: bool | None = None


@router.get("/corpuses", response_model=List[CorpusInfo])
async def list_corpuses():
    """
    List all available text corpuses with status information.
    
    Returns:
        List of corpus information including status, chunk count, etc.
    """
    registry = get_registry()
    corpuses = []
    
    # list_corpuses() returns list of dicts, not names
    corpus_list = registry.list_corpuses()
    
    for corpus_dict in corpus_list:
        corpus_name = corpus_dict['name']
        corpus_config = registry.get_corpus(corpus_name)
        if not corpus_config:
            continue
        
        # Get status
        status_info = registry.check_corpus_status(corpus_name)
        
        corpuses.append(CorpusInfo(
            name=corpus_config.name,
            display_name=corpus_config.display_name,
            description=corpus_config.description,
            is_active=corpus_config.is_active,
            chunk_count=status_info.chunk_count if status_info else 0,
            last_processed=corpus_config.last_processed,
            needs_rebuild=status_info.needs_rebuild if status_info else False,
            missing_components=status_info.missing_components if status_info else []
        ))
    
    return corpuses


@router.post("/corpuses", status_code=status.HTTP_202_ACCEPTED)
async def create_corpus(
    corpus_request: CorpusCreateRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger ingestion of a new corpus.
    
    This endpoint validates the request and adds the corpus to the registry.
    The actual ingestion happens asynchronously via background task.
    
    Args:
        corpus_request: Corpus configuration
        background_tasks: FastAPI background tasks
    
    Returns:
        Confirmation that ingestion has been queued
    """
    registry = get_registry()
    
    # Check if corpus already exists
    if registry.get_corpus(corpus_request.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Corpus '{corpus_request.name}' already exists"
        )
    
    # Validate source file exists
    from pathlib import Path
    from config.settings import settings
    
    source_path = settings.data_path.parent / corpus_request.source_file
    if not source_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source file not found: {corpus_request.source_file}"
        )
    
    # Add to registry (marks as inactive until ingestion completes)
    try:
        registry.add_corpus(
            name=corpus_request.name,
            display_name=corpus_request.display_name,
            description=corpus_request.description,
            source_file=corpus_request.source_file,
            file_type=corpus_request.file_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add corpus to registry: {str(e)}"
        )
    
    # TODO: Queue background ingestion task
    # background_tasks.add_task(ingest_corpus, corpus_request.name)
    
    return {
        "success": True,
        "message": f"Corpus '{corpus_request.name}' created. Ingestion queued.",
        "note": "Corpus will be inactive until ingestion completes. Use batch_ingest.py to process."
    }


@router.put("/corpuses/{name}")
async def update_corpus(name: str, update_request: CorpusUpdateRequest):
    """
    Update corpus metadata.
    
    Args:
        name: Corpus name
        update_request: Fields to update
    
    Returns:
        Updated corpus information
    """
    registry = get_registry()
    corpus = registry.get_corpus(name)
    
    if not corpus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Corpus '{name}' not found"
        )
    
    # Update fields
    updated = False
    if update_request.display_name is not None:
        corpus.display_name = update_request.display_name
        updated = True
    if update_request.description is not None:
        corpus.description = update_request.description
        updated = True
    if update_request.is_active is not None:
        corpus.is_active = update_request.is_active
        updated = True
    
    if updated:
        registry.update_corpus(corpus)
    
    return {
        "success": True,
        "message": f"Corpus '{name}' updated successfully",
        "corpus": {
            "name": corpus.name,
            "display_name": corpus.display_name,
            "description": corpus.description,
            "is_active": corpus.is_active
        }
    }


@router.delete("/corpuses/{name}")
async def delete_corpus(name: str, delete_data: bool = False):
    """
    Delete a corpus.
    
    Args:
        name: Corpus name
        delete_data: If True, also delete associated data files (ChromaDB, BM25, chunks)
    
    Returns:
        Success confirmation
    """
    registry = get_registry()
    corpus = registry.get_corpus(name)
    
    if not corpus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Corpus '{name}' not found"
        )
    
    # Remove from registry
    try:
        registry.remove_corpus(name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove corpus from registry: {str(e)}"
        )
    
    # Optionally delete data files
    if delete_data:
        import shutil
        from pathlib import Path
        
        try:
            # Delete ChromaDB
            if Path(corpus.chroma_db_path).exists():
                shutil.rmtree(corpus.chroma_db_path)
            
            # Delete BM25 index
            if Path(corpus.bm25_index_path).exists():
                Path(corpus.bm25_index_path).unlink()
            
            # Delete cached chunks
            if Path(corpus.cache_dir).exists():
                shutil.rmtree(corpus.cache_dir)
        except Exception as e:
            return {
                "success": True,
                "message": f"Corpus '{name}' removed from registry, but failed to delete data files",
                "error": str(e)
            }
    
    return {
        "success": True,
        "message": f"Corpus '{name}' deleted successfully",
        "data_deleted": delete_data
    }

