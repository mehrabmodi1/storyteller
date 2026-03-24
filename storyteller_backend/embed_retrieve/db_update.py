"""
ChromaDB Migration Script (Wrapper for chroma-migrate)

Purpose: Migrate ChromaDB collections to be compatible with ChromaDB 0.5.x

Background:
-----------
ChromaDB 0.5.x introduced breaking changes to the collection configuration schema.
Collections created with earlier versions need to be migrated using the official
chroma-migrate tool.

This script wraps chroma-migrate to:
- Migrate all corpus databases in the data directory
- Create backups before migration
- Provide progress reporting and summaries

Usage:
------
    # Install dependencies first
    pip install chroma-migrate
    
    # Migrate all corpus databases
    python -m embed_retrieve.db_update
    
    # Migrate specific corpus
    python -m embed_retrieve.db_update --corpus jataka_tales
    
    # Skip backups (not recommended)
    python -m embed_retrieve.db_update --no-backup

Requirements:
-------------
- chroma-migrate>=0.0.12
- chromadb>=0.5.23

References:
-----------
- chroma-migrate: https://github.com/chroma-core/chroma-migrate
- ChromaDB migration docs: https://www.trychroma.com/migration

Author: ChromaDB migration wrapper
Date: 2025-12-22
"""

import subprocess
import sys
import argparse
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import shutil


def backup_database_directory(db_dir: Path) -> Path:
    """
    Create a backup of an entire corpus database directory.
    
    Args:
        db_dir: Path to the corpus database directory (e.g., data/chroma_db/jataka_tales)
        
    Returns:
        Path to the backup directory
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = db_dir.parent / f"{db_dir.name}_backup_{timestamp}"
    
    shutil.copytree(db_dir, backup_dir)
    print(f"✓ Created backup: {backup_dir}")
    return backup_dir


def check_chroma_migrate_installed() -> bool:
    """
    Check if chroma-migrate is installed.
    
    Returns:
        True if installed, False otherwise
    """
    try:
        import chroma_migrate
        return True
    except ImportError:
        return False


def migrate_database(db_path: Path, create_backup: bool = True) -> Dict:
    """
    Migrate a single ChromaDB database using chroma-migrate.
    
    Args:
        db_path: Path to the chroma.sqlite3 file
        create_backup: If True, create a backup before migrating
        
    Returns:
        Dictionary with migration result
    """
    corpus_name = db_path.parent.name
    
    print(f"\n{'='*70}")
    print(f"Processing corpus: {corpus_name}")
    print(f"Database: {db_path}")
    print(f"{'='*70}")
    
    if not db_path.exists():
        print(f"✗ Database not found: {db_path}")
        return {"corpus": corpus_name, "status": "not_found", "error": "Database file not found"}
    
    # Create backup
    if create_backup:
        try:
            backup_database_directory(db_path.parent)
        except Exception as e:
            print(f"⚠ Warning: Failed to create backup: {e}")
            print(f"  Continuing with migration...")
    
    # Run chroma-migrate
    print(f"\nRunning chroma-migrate for {corpus_name}...")
    
    try:
        # chroma-migrate expects the directory containing chroma.sqlite3
        db_dir = str(db_path.parent)
        
        # Use sys.executable to ensure we use the current Python environment
        result = subprocess.run(
            [sys.executable, "-m", "chroma_migrate", db_dir],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"✓ Migration completed successfully")
            print(f"  Output: {result.stdout.strip()}")
            return {"corpus": corpus_name, "status": "success", "output": result.stdout}
        else:
            error_msg = result.stderr.strip() or result.stdout.strip()
            print(f"✗ Migration failed")
            print(f"  Error: {error_msg}")
            return {"corpus": corpus_name, "status": "failed", "error": error_msg}
            
    except subprocess.TimeoutExpired:
        error_msg = "Migration timed out after 60 seconds"
        print(f"✗ {error_msg}")
        return {"corpus": corpus_name, "status": "timeout", "error": error_msg}
    
    except Exception as e:
        error_msg = str(e)
        print(f"✗ Unexpected error: {error_msg}")
        return {"corpus": corpus_name, "status": "error", "error": error_msg}


def find_corpus_databases(data_dir: Path) -> List[Path]:
    """
    Find all ChromaDB databases in the data directory.
    
    Args:
        data_dir: Path to the data directory (should point to the 'data' folder)
        
    Returns:
        List of paths to chroma.sqlite3 files
    """
    chroma_db_dir = data_dir / "chroma_db"
    
    if not chroma_db_dir.exists():
        print(f"✗ ChromaDB directory not found: {chroma_db_dir}")
        return []
    
    databases = list(chroma_db_dir.glob("*/chroma.sqlite3"))
    return sorted(databases)


def main():
    parser = argparse.ArgumentParser(
        description="Migrate ChromaDB collections using chroma-migrate"
    )
    parser.add_argument(
        "--corpus",
        type=str,
        help="Migrate only a specific corpus (e.g., 'jataka_tales')"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backups (not recommended)"
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*70}")
    print(f"ChromaDB Migration Script (chroma-migrate wrapper)")
    print(f"{'='*70}")
    
    # Check if chroma-migrate is installed
    if not check_chroma_migrate_installed():
        print("\n✗ ERROR: chroma-migrate is not installed")
        print("\nPlease install it first:")
        print("  pip install chroma-migrate")
        print("\nOr install all backend dependencies:")
        print("  pip install -r requirements.txt")
        return 1
    
    print("✓ chroma-migrate is installed")
    
    # Determine data directory
    try:
        from config.settings import settings
        data_dir = settings.data_path
    except ImportError:
        data_dir = Path(__file__).parent.parent.parent / "data"
    
    print(f"Data directory: {data_dir}")
    print(f"Backup: {'Disabled' if args.no_backup else 'Enabled'}")
    
    # Find databases
    databases = find_corpus_databases(data_dir)
    
    if args.corpus:
        # Filter to specific corpus
        databases = [db for db in databases if args.corpus in str(db)]
        if not databases:
            print(f"\n✗ No database found for corpus: {args.corpus}")
            return 1
    
    if not databases:
        print("\n✗ No ChromaDB databases found")
        return 1
    
    print(f"\nFound {len(databases)} database(s) to migrate")
    
    # Migrate each database
    results = []
    for db_path in databases:
        result = migrate_database(db_path, create_backup=not args.no_backup)
        results.append(result)
    
    # Summary
    print(f"\n{'='*70}")
    print(f"Migration Summary")
    print(f"{'='*70}")
    
    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = sum(1 for r in results if r["status"] in ["failed", "timeout", "error"])
    
    print(f"Total databases processed: {len(results)}")
    print(f"Successful migrations: {success_count}")
    print(f"Failed migrations: {failed_count}")
    
    if failed_count > 0:
        print(f"\n⚠ Some migrations failed:")
        for result in results:
            if result["status"] != "success":
                print(f"  - {result['corpus']}: {result.get('error', 'Unknown error')}")
    
    if success_count == len(results):
        print(f"\n✓ All migrations completed successfully!")
        return 0
    else:
        print(f"\n⚠ {failed_count} migration(s) failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit(main())
