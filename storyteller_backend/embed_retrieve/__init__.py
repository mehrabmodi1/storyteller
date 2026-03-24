"""
Embed & Retrieve Package

Handles corpus management, text processing, embedding generation,
and hybrid retrieval (ChromaDB + BM25) for RAG-based story generation.

Key modules:
- retriever: Hybrid search combining semantic and keyword retrieval
- corpus_registry: Centralized corpus metadata and status management
- batch_ingest: Bulk corpus processing and indexing
- build_database: Single corpus database builder
"""

from .retriever import HybridRetriever
from .corpus_registry import get_registry, CorpusRegistry

__all__ = [
    "HybridRetriever",
    "get_registry",
    "CorpusRegistry",
]

