# Configuration for the data processing pipeline

# --- Chunking Parameters ---
# The target size of each text chunk in tokens
CHUNK_SIZE = 1000

# The overlap between consecutive chunks in tokens
CHUNK_OVERLAP = 200

# --- Contextualization Parameters ---
# The size of the larger window around a chunk to generate context from
CONTEXT_WINDOW_SIZE = 5000

# The approximate number of tokens for the generated context summary
CONTEXT_SUMMARY_TOKENS = 200

# --- OpenAI Model Parameters ---
# Model for generating embeddings
EMBEDDING_MODEL = "text-embedding-3-small"

# Model for generating contextual summaries
CONTEXT_MODEL = "gpt-4o-mini"

# --- Path Parameters ---
# Directory to cache processed chunks to avoid re-running API calls
CACHE_DIR = "data/processed_chunks"

# Directory to store the persistent ChromaDB database
CHROMA_DB_PATH = "data/chroma_db"

# Name of the collection within ChromaDB
CHROMA_COLLECTION_NAME = "mahabharata_chunks"

# Path to the source PDF document to be processed
PDF_PATH = "raw_texts/The Complete Mahabharata .pdf"

# Path to store the serialized BM25 index
BM25_INDEX_PATH = "data/bm25_index.pkl" 