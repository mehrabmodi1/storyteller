# Configuration for the data processing pipeline

# --- Chunking Parameters ---
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# --- Contextualization Parameters ---
CONTEXT_WINDOW_SIZE = 5000
CONTEXT_SUMMARY_TOKENS = 200

# --- Path Parameters ---
CACHE_DIR = "../data/processed_chunks"
