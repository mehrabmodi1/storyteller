# Configuration for the data processing pipeline

from config.settings import settings

# --- Chunking Parameters ---
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# --- Contextualization Parameters ---
CONTEXT_WINDOW_SIZE = 5000
CONTEXT_SUMMARY_TOKENS = 200

# --- Path Parameters ---
CACHE_DIR = "../data/processed_chunks"

def get_chroma_db_path() -> str:
    """Provider-namespaced ChromaDB path."""
    return f"../data/chroma_db_{settings.provider}"

CHROMA_COLLECTION_NAME = "mahabharata_chunks"
PDF_PATH = "../raw_texts/The Complete Mahabharata .pdf"
BM25_INDEX_PATH = "../data/bm25_index.pkl" 