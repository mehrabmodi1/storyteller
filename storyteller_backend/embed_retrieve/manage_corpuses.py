"""
Corpus Management Utility

This script provides utilities for managing corpuses in the storyteller application.
It can add new corpuses, list existing ones, and build them.
"""

import argparse
import os
from datetime import datetime
from .corpus_registry import CorpusConfig, get_registry
from .build_database import build_corpus


def add_corpus(name: str, display_name: str, description: str, source_file: str, 
               file_type: str = "pdf") -> bool:
    """
    Add a new corpus to the registry.
    
    Args:
        name: Unique identifier for the corpus
        display_name: Human-readable name
        description: Description of the corpus
        source_file: Path to the source file
        file_type: Type of file ("pdf" or "text")
    
    Returns:
        True if successful, False otherwise
    """
    registry = get_registry()
    
    # Validate source file exists
    if not os.path.exists(source_file):
        print(f"Error: Source file '{source_file}' does not exist.")
        return False
    
    # Create corpus configuration
    corpus_config = CorpusConfig(
        name=name,
        display_name=display_name,
        description=description,
        source_file=source_file,
        file_type=file_type,
        collection_name=f"{name}_chunks",
        cache_dir=f"data/processed_chunks/{name}",
        bm25_index_path=f"data/bm25_indexes/{name}_bm25.pkl",
        is_active=True,
        created_at=datetime.now().isoformat()
    )
    
    # Add to registry
    success = registry.add_corpus(corpus_config)
    if success:
        print(f"Successfully added corpus '{display_name}' to registry.")
        print(f"Collection name: {corpus_config.collection_name}")
        print(f"Cache directory: {corpus_config.cache_dir}")
        print(f"BM25 index path: {corpus_config.bm25_index_path}")
    else:
        print(f"Failed to add corpus '{name}' - it may already exist.")
    
    return success


def list_corpuses():
    """List all corpuses in the registry."""
    registry = get_registry()
    corpuses = registry.list_corpuses()
    
    if not corpuses:
        print("No corpuses found in registry.")
        return
    
    print("Available corpuses:")
    print("-" * 80)
    for corpus in corpuses:
        print(f"Name: {corpus['name']}")
        print(f"Display Name: {corpus['display_name']}")
        print(f"Description: {corpus['description']}")
        print(f"Active: {corpus['is_active']}")
        print(f"Chunk Count: {corpus['chunk_count']}")
        print(f"Last Processed: {corpus['last_processed'] or 'Never'}")
        print("-" * 80)


def main():
    """Main function for the corpus management utility."""
    parser = argparse.ArgumentParser(description="Manage corpuses for the storyteller application.")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add corpus command
    add_parser = subparsers.add_parser('add', help='Add a new corpus')
    add_parser.add_argument('name', help='Unique identifier for the corpus')
    add_parser.add_argument('display_name', help='Human-readable name')
    add_parser.add_argument('description', help='Description of the corpus')
    add_parser.add_argument('source_file', help='Path to the source file')
    add_parser.add_argument('--file-type', choices=['pdf', 'text'], default='pdf',
                           help='Type of source file (default: pdf)')
    
    # List corpuses command
    subparsers.add_parser('list', help='List all corpuses')
    
    # Build corpus command
    build_parser = subparsers.add_parser('build', help='Build a corpus')
    build_parser.add_argument('name', help='Name of the corpus to build')
    build_parser.add_argument('--force-rebuild', action='store_true',
                             help='Force rebuild even if index exists')
    
    args = parser.parse_args()
    
    if args.command == 'add':
        add_corpus(args.name, args.display_name, args.description, 
                  args.source_file, args.file_type)
    elif args.command == 'list':
        list_corpuses()
    elif args.command == 'build':
        build_corpus(args.name, args.force_rebuild)
    else:
        parser.print_help()


if __name__ == '__main__':
    main() 