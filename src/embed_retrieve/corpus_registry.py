"""
Corpus Registry System

This module manages multiple corpuses for the storyteller application.
Each corpus has its own configuration, file paths, and metadata.
"""

import os
import json
import yaml
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import chromadb


@dataclass
class CorpusConfig:
    """Configuration for a single corpus."""
    name: str
    display_name: str
    description: str
    source_file: str  # Path to the source file (PDF or text)
    file_type: str  # "pdf" or "text"
    collection_name: str  # ChromaDB collection name
    cache_dir: str  # Directory for processed chunks
    bm25_index_path: str  # Path to BM25 index file
    chroma_db_path: str  # Path to ChromaDB database directory
    is_active: bool = True
    created_at: Optional[str] = None
    last_processed: Optional[str] = None
    chunk_count: int = 0


@dataclass
class CorpusStatus:
    """Status information for a corpus."""
    name: str
    display_name: str
    chunks_exist: bool
    chroma_exists: bool
    bm25_exists: bool
    needs_rebuild: bool
    missing_components: List[str]
    chunk_count: int
    last_processed: Optional[str] = None


class CorpusRegistry:
    """Manages multiple corpuses for the storyteller application."""
    
    def __init__(self, registry_file: str = "data/corpus_registry.json"):
        self.registry_file = registry_file
        self.corpuses: Dict[str, CorpusConfig] = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load the corpus registry from file."""
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                    for corpus_data in data.get('corpuses', []):
                        corpus = CorpusConfig(**corpus_data)
                        self.corpuses[corpus.name] = corpus
            except Exception as e:
                print(f"Error loading corpus registry: {e}")
                self._create_default_registry()
        else:
            self._create_default_registry()
    
    def _create_default_registry(self):
        """Create the default registry with the existing Mahabharata corpus."""
        from datetime import datetime
        
        mahabharata_config = CorpusConfig(
            name="mahabharata",
            display_name="The Mahabharata",
            description="An ancient Indian epic that tells the story of the Kurukshetra War and the fates of the Kaurava and Pandava princes.",
            source_file="raw_texts/The Complete Mahabharata .pdf",
            file_type="pdf",
            collection_name="mahabharata_chunks",
            cache_dir="data/processed_chunks",  # Use existing flat structure
            bm25_index_path="data/bm25_index.pkl",  # Use existing BM25 index path
            chroma_db_path="data/chroma_db", # Default for default corpus
            is_active=True,
            created_at=datetime.now().isoformat(),
            last_processed=datetime.now().isoformat()
        )
        
        self.corpuses["mahabharata"] = mahabharata_config
        self._save_registry()
    
    def _save_registry(self):
        """Save the corpus registry to file."""
        os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
        with open(self.registry_file, 'w') as f:
            json.dump({
                'corpuses': [asdict(corpus) for corpus in self.corpuses.values()]
            }, f, indent=2)
    
    def load_jobs_from_yaml(self, jobs_file: str = "jobs.yaml"):
        """Load corpus configurations from a YAML jobs file."""
        if not os.path.exists(jobs_file):
            print(f"Jobs file '{jobs_file}' not found.")
            return False
        
        try:
            with open(jobs_file, 'r') as f:
                jobs_data = yaml.safe_load(f)
            
            corpuses_data = jobs_data.get('corpuses', {})
            added_count = 0
            
            for name, config_data in corpuses_data.items():
                if not config_data.get('is_active', True):
                    continue
                
                # Create corpus configuration
                corpus_config = CorpusConfig(
                    name=name,
                    display_name=config_data['display_name'],
                    description=config_data['description'],
                    source_file=config_data['source_file'],
                    file_type=config_data['file_type'],
                    collection_name=f"{name}_chunks",
                    cache_dir=config_data.get('cache_dir', f"data/processed_chunks/{name}"),
                    bm25_index_path=config_data.get('bm25_index_path', f"data/bm25_indexes/{name}_bm25.pkl"),
                    chroma_db_path=config_data.get('chroma_db_path', f"data/chroma_db/{name}"),
                    is_active=config_data.get('is_active', True),
                    created_at=self.corpuses.get(name, CorpusConfig).created_at or None
                )
                
                # Add or update in registry
                if name in self.corpuses:
                    # Update existing corpus
                    existing = self.corpuses[name]
                    corpus_config.created_at = existing.created_at
                    corpus_config.last_processed = existing.last_processed
                    corpus_config.chunk_count = existing.chunk_count
                    print(f"Updated existing corpus: {name}")
                else:
                    # Add new corpus
                    from datetime import datetime
                    corpus_config.created_at = datetime.now().isoformat()
                    print(f"Added new corpus: {name}")
                
                # Ensure all necessary directories exist for this corpus
                os.makedirs(corpus_config.cache_dir, exist_ok=True)
                os.makedirs(os.path.dirname(corpus_config.bm25_index_path), exist_ok=True)
                os.makedirs(corpus_config.chroma_db_path, exist_ok=True)
                
                self.corpuses[name] = corpus_config
                added_count += 1
            
            self._save_registry()
            print(f"Loaded {added_count} corpuses from jobs file.")
            return True
            
        except Exception as e:
            print(f"Error loading jobs from YAML: {e}")
            return False
    
    def check_corpus_status(self, corpus_name: str) -> Optional[CorpusStatus]:
        """Check the status of a specific corpus and what needs rebuilding."""
        corpus_config = self.get_corpus(corpus_name)
        if not corpus_config:
            return None
        
        # Check if chunks exist
        chunks_exist = (os.path.exists(corpus_config.cache_dir) and 
                       len([f for f in os.listdir(corpus_config.cache_dir) if f.endswith('.json')]) > 0)
        
        # Check if ChromaDB collection exists
        try:
            chroma_client = chromadb.PersistentClient(path=corpus_config.chroma_db_path)
            collections = chroma_client.list_collections()
            chroma_exists = any(col.name == corpus_config.collection_name for col in collections)
        except Exception:
            chroma_exists = False
        
        # Check if BM25 index exists
        bm25_exists = os.path.exists(corpus_config.bm25_index_path)
        
        # Determine missing components
        missing_components = []
        if not chunks_exist:
            missing_components.append('chunks')
        if not chroma_exists:
            missing_components.append('chroma')
        if not bm25_exists:
            missing_components.append('bm25')
        
        return CorpusStatus(
            name=corpus_name,
            display_name=corpus_config.display_name,
            chunks_exist=chunks_exist,
            chroma_exists=chroma_exists,
            bm25_exists=bm25_exists,
            needs_rebuild=len(missing_components) > 0,
            missing_components=missing_components,
            chunk_count=corpus_config.chunk_count,
            last_processed=corpus_config.last_processed
        )
    
    def get_all_corpus_statuses(self) -> List[CorpusStatus]:
        """Get status for all corpuses."""
        statuses = []
        for corpus_name in self.corpuses.keys():
            status = self.check_corpus_status(corpus_name)
            if status:
                statuses.append(status)
        return statuses
    
    def add_corpus(self, config: CorpusConfig) -> bool:
        """Add a new corpus to the registry."""
        if config.name in self.corpuses:
            print(f"Corpus '{config.name}' already exists.")
            return False
        
        # Ensure all necessary directories exist
        os.makedirs(config.cache_dir, exist_ok=True)
        os.makedirs(os.path.dirname(config.bm25_index_path), exist_ok=True)
        os.makedirs(config.chroma_db_path, exist_ok=True)
        
        self.corpuses[config.name] = config
        self._save_registry()
        return True
    
    def get_corpus(self, name: str) -> Optional[CorpusConfig]:
        """Get a corpus by name."""
        return self.corpuses.get(name)
    
    def get_active_corpuses(self) -> List[CorpusConfig]:
        """Get all active corpuses."""
        return [corpus for corpus in self.corpuses.values() if corpus.is_active]
    
    def list_corpuses(self) -> List[Dict]:
        """List all corpuses with their metadata."""
        return [
            {
                'name': corpus.name,
                'display_name': corpus.display_name,
                'description': corpus.description,
                'is_active': corpus.is_active,
                'chunk_count': corpus.chunk_count,
                'last_processed': corpus.last_processed
            }
            for corpus in self.corpuses.values()
        ]
    
    def update_corpus(self, name: str, **kwargs) -> bool:
        """Update a corpus configuration."""
        if name not in self.corpuses:
            return False
        
        corpus = self.corpuses[name]
        for key, value in kwargs.items():
            if hasattr(corpus, key):
                setattr(corpus, key, value)
        
        self._save_registry()
        return True
    
    def delete_corpus(self, name: str) -> bool:
        """Delete a corpus from the registry."""
        if name not in self.corpuses:
            return False
        
        del self.corpuses[name]
        self._save_registry()
        return True
    
    def get_corpus_by_collection_name(self, collection_name: str) -> Optional[CorpusConfig]:
        """Get a corpus by its ChromaDB collection name."""
        for corpus in self.corpuses.values():
            if corpus.collection_name == collection_name:
                return corpus
        return None


# Global registry instance
registry = CorpusRegistry()


def get_registry() -> CorpusRegistry:
    """Get the global corpus registry instance."""
    return registry 