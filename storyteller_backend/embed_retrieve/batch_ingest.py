"""
Batch Corpus Ingestion Script

This script loads corpus configurations from jobs.yaml and processes them
with progress tracking and smart recovery capabilities.
"""

import argparse
import os
import sys
from typing import List, Dict
from tqdm import tqdm
from datetime import datetime

from .corpus_registry import get_registry, CorpusStatus
from .build_database import build_corpus


def print_corpus_status(status: CorpusStatus):
    """Print a formatted status for a corpus."""
    print(f"\n📚 {status.display_name} ({status.name})")
    print(f"   Chunks: {'✅' if status.chunks_exist else '❌'}")
    print(f"   ChromaDB: {'✅' if status.chroma_exists else '❌'}")
    print(f"   BM25: {'✅' if status.bm25_exists else '❌'}")
    
    if status.needs_rebuild:
        print(f"   🔧 Missing: {', '.join(status.missing_components)}")
    else:
        print(f"   ✅ Complete ({status.chunk_count} chunks)")
    
    if status.last_processed:
        print(f"   📅 Last processed: {status.last_processed}")


def print_summary(statuses: List[CorpusStatus]):
    """Print a summary of all corpus statuses."""
    print("\n" + "="*80)
    print("📊 CORPUS STATUS SUMMARY")
    print("="*80)
    
    total_corpuses = len(statuses)
    complete_corpuses = sum(1 for s in statuses if not s.needs_rebuild)
    needs_rebuild = sum(1 for s in statuses if s.needs_rebuild)
    
    print(f"Total corpuses: {total_corpuses}")
    print(f"Complete: {complete_corpuses}")
    print(f"Needs rebuild: {needs_rebuild}")
    
    if needs_rebuild > 0:
        print(f"\n🔧 Corpuses needing rebuild:")
        for status in statuses:
            if status.needs_rebuild:
                print(f"   - {status.display_name}: {', '.join(status.missing_components)}")
    
    print("="*80)


def batch_ingest(jobs_file: str = "jobs.yaml", force_rebuild: bool = False, 
                specific_corpus: str = None, dry_run: bool = False):
    """
    Main batch ingestion function.
    
    Args:
        jobs_file: Path to the YAML jobs file
        force_rebuild: Whether to force rebuild all corpuses
        specific_corpus: If specified, only process this corpus
        dry_run: If True, only show status without processing
    """
    registry = get_registry()
    
    # Load jobs from YAML
    print(f"📋 Loading jobs from {jobs_file}...")
    if not registry.load_jobs_from_yaml(jobs_file):
        print("❌ Failed to load jobs file.")
        return False
    
    # Get all corpus statuses
    print("🔍 Checking corpus statuses...")
    statuses = registry.get_all_corpus_statuses()
    
    # Print current status
    print_summary(statuses)
    
    if dry_run:
        print("\n🔍 DRY RUN - No processing will be performed.")
        return True
    
    # Filter corpuses to process
    corpuses_to_process = []
    if specific_corpus:
        # Process only specific corpus
        target_status = next((s for s in statuses if s.name == specific_corpus), None)
        if not target_status:
            print(f"❌ Corpus '{specific_corpus}' not found.")
            return False
        corpuses_to_process = [target_status]
    else:
        # Process all corpuses that need rebuilding
        corpuses_to_process = [s for s in statuses if s.needs_rebuild or force_rebuild]
    
    if not corpuses_to_process:
        print("✅ All corpuses are up to date!")
        return True
    
    # Process corpuses with progress tracking
    print(f"\n🚀 Processing {len(corpuses_to_process)} corpus(es)...")
    
    success_count = 0
    failed_corpuses = []
    
    for status in tqdm(corpuses_to_process, desc="Processing corpuses"):
        corpus_name = status.name
        display_name = status.display_name
        
        tqdm.write(f"\n🔄 Processing: {display_name}")
        
        try:
            # Build the corpus
            success = build_corpus(corpus_name, force_rebuild)
            
            if success:
                success_count += 1
                tqdm.write(f"✅ Successfully processed: {display_name}")
            else:
                failed_corpuses.append(corpus_name)
                tqdm.write(f"❌ Failed to process: {display_name}")
                
        except Exception as e:
            failed_corpuses.append(corpus_name)
            tqdm.write(f"❌ Error processing {display_name}: {str(e)}")
    
    # Print final summary
    print(f"\n🎉 BATCH INGESTION COMPLETE")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {len(failed_corpuses)}")
    
    if failed_corpuses:
        print(f"Failed corpuses: {', '.join(failed_corpuses)}")
    
    return len(failed_corpuses) == 0


def main():
    """Main function for the batch ingestion script."""
    parser = argparse.ArgumentParser(
        description="Batch corpus ingestion for the storyteller application."
    )
    parser.add_argument(
        '--jobs-file',
        default='src/embed_retrieve/jobs.yaml',
        help='Path to the YAML jobs file (default: src/embed_retrieve/jobs.yaml)'
    )
    parser.add_argument(
        '--force-rebuild',
        action='store_true',
        help='Force rebuild all corpuses even if they appear complete'
    )
    parser.add_argument(
        '--corpus',
        type=str,
        help='Process only a specific corpus by name'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show status without processing any corpuses'
    )
    parser.add_argument(
        '--status-only',
        action='store_true',
        help='Show status of all corpuses and exit'
    )
    
    args = parser.parse_args()
    
    if args.status_only:
        # Just show status
        registry = get_registry()
        registry.load_jobs_from_yaml(args.jobs_file)
        statuses = registry.get_all_corpus_statuses()
        print_summary(statuses)
        return
    
    # Run batch ingestion
    success = batch_ingest(
        jobs_file=args.jobs_file,
        force_rebuild=args.force_rebuild,
        specific_corpus=args.corpus,
        dry_run=args.dry_run
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main() 