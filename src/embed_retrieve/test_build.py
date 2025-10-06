import os
import sys
import time

# Add the project root to the Python path to allow for package-like imports.
# This allows us to run this script directly from the command line.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.embed_retrieve.build_database import HybridRetrieverBuilder
from src.embed_retrieve.config import CACHE_DIR

def run_test():
    """
    Instantiates and runs the builder to test the full, resumable pipeline.
    """
    # This path is relative to the project root, where this script should be run from.
    MAHABHARATA_PATH = "raw_texts/The Complete Mahabharata .pdf"
    
    print("--- Starting Test ---")
    
    if not os.path.exists(MAHABHARATA_PATH):
        print(f"Error: PDF file not found at '{MAHABHARATA_PATH}'")
        print("Please ensure you are running this script from the project's root directory.")
        return

    builder = HybridRetrieverBuilder(pdf_path=MAHABHARATA_PATH)
    
    # --- Modify the builder to only process a few chunks for testing ---
    # We will process the first 10 chunks. Since the first 5 are already
    # cached from the previous run, this will test the continuation logic.
    builder._load_and_tokenize_text()
    builder._create_initial_chunks()
    builder.chunks = builder.chunks[:10] # Limit to first 10 chunks for the test
    print(f"\n--- TESTING WITH A SUBSET OF 10 CHUNKS ---\n")

    # Run the full build process on the subset
    print("Running the build process. Expecting 5 cache hits, then 5 misses...")
    builder.build_from_existing_chunks() # We use the helper for the test
    
    print("\n--- Test Complete ---")
    print("Check the output above for 'Cache HIT' and 'Cache MISS' messages.")

if __name__ == '__main__':
    run_test() 