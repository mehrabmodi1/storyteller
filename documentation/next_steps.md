# Multi-Corpus Embedding System Documentation

## Overview

The storyteller application now supports multiple corpuses with isolated embedding collections and BM25 indexes. Each corpus has its own dedicated directories and databases, ensuring complete separation and easy management.

## Current Corpus Status

As of the latest ingestion, the following corpuses are available:

| Corpus | Display Name | Status | Chunks | ChromaDB | BM25 |
|--------|--------------|--------|--------|----------|------|
| `mahabharata` | The Mahabharata | ✅ Complete | ✅ | ✅ | ✅ |
| `odyssey` | The Odyssey | ✅ Complete | ✅ | ✅ | ✅ |
| `arabian_nights` | The Arabian Nights | ✅ Complete | ✅ | ✅ | ✅ |
| `volsunga_saga` | The Volsunga Saga | ✅ Complete | ✅ | ✅ | ✅ |
| `jataka_tales` | The Jataka Tales | ✅ Complete | ✅ | ✅ | ✅ |
| `locus_platform_docs` | Locus Platform Documentation | ✅ Complete | ✅ | ✅ | ✅ |

## Directory Structure

```
data/
├── corpus_registry.json              # Central registry of all corpuses
├── processed_chunks/
│   ├── mahabharata/                  # Mahabharata chunk files
│   ├── odyssey/                      # Odyssey chunk files
│   ├── arabian_nights/               # Arabian Nights chunk files
│   ├── volsunga_saga/                # Volsunga Saga chunk files
│   ├── jataka_tales/                 # Jataka Tales chunk files
│   └── locus_platform_docs/          # Locus Platform Documentation chunk files
├── bm25_indexes/
│   ├── mahabharata_bm25.pkl          # Mahabharata BM25 index
│   ├── odyssey_bm25.pkl              # Odyssey BM25 index
│   ├── arabian_nights_bm25.pkl       # Arabian Nights BM25 index
│   ├── volsunga_saga_bm25.pkl        # Volsunga Saga BM25 index
│   ├── jataka_tales_bm25.pkl         # Jataka Tales BM25 index
│   └── locus_platform_docs_bm25.pkl  # Locus Platform Documentation BM25 index
└── chroma_db/
    ├── mahabharata/                  # Mahabharata ChromaDB database
    ├── odyssey/                      # Odyssey ChromaDB database
    ├── arabian_nights/               # Arabian Nights ChromaDB database
    ├── volsunga_saga/                # Volsunga Saga ChromaDB database
    ├── jataka_tales/                 # Jataka Tales ChromaDB database
    └── locus_platform_docs/          # Locus Platform Documentation ChromaDB database
```

## Configuration Management

### Jobs Configuration (`src/embed_retrieve/jobs.yaml`)

Each corpus is configured in the YAML file with the following structure:

```yaml
corpus_name:
  display_name: "Human Readable Name"
  description: "Description of the corpus content"
  source_file: "path/to/source/file"
  file_type: "pdf" or "text"
  is_active: true or false
  cache_dir: "data/processed_chunks/corpus_name"
  bm25_index_path: "data/bm25_indexes/corpus_name_bm25.pkl"
  chroma_db_path: "data/chroma_db/corpus_name"
```

### Corpus Registry (`data/corpus_registry.json`)

The system maintains a central registry that tracks:
- Corpus metadata (name, description, file paths)
- Processing status (last processed, chunk count)
- Active/inactive status

## Multi-File Corpus Support

### Preprocessing Tool

For corpuses with multiple source files, use the preprocessing tool:

```bash
python -m src.embed_retrieve.preprocess_multi_files
```

This tool:
1. Detects folders in `raw_texts/` containing multiple files
2. Concatenates all files into a single output file
3. Names the output file as `{folder_name}_concatenated.{ext}`

### Workflow for Multi-File Corpuses

1. **Create folder**: `raw_texts/my_corpus/`
2. **Add files**: Place all `.txt` or `.pdf` files in the folder
3. **Run preprocessing**: `python -m src.embed_retrieve.preprocess_multi_files`
4. **Add to jobs.yaml**: Configure the concatenated file
5. **Ingest**: `python -m src.embed_retrieve.batch_ingest --corpus my_corpus`

## Ingestion Management

### Batch Ingestion Commands

```bash
# Check status of all corpuses
python -m src.embed_retrieve.batch_ingest --status-only

# Process all corpuses that need rebuilding
python -m src.embed_retrieve.batch_ingest

# Process specific corpus
python -m src.embed_retrieve.batch_ingest --corpus corpus_name

# Force rebuild (even if complete)
python -m src.embed_retrieve.batch_ingest --force-rebuild

# Dry run (show what would be processed)
python -m src.embed_retrieve.batch_ingest --dry-run
```

### Smart Recovery System

The system intelligently handles partial failures:
- **Chunks missing but ChromaDB exists**: Rebuilds chunks, skips re-embedding
- **Chunks exist but ChromaDB missing**: Re-embeds existing chunks
- **BM25 missing**: Rebuilds BM25 from existing chunks
- **Everything missing**: Full rebuild

## Integration with Storyteller Application

### Next Steps for Application Integration

1. **Update Retriever Class**
   - Modify `src/embed_retrieve/retriever.py` to accept a corpus name parameter
   - Load the appropriate ChromaDB collection and BM25 index based on corpus name

2. **Update Agent Graph**
   - Modify `src/agent/graph.py` to support corpus switching
   - Add corpus selection to the state management

3. **Update API Endpoints**
   - Add corpus selection to the FastAPI endpoints
   - Implement corpus switching functionality

4. **Update Frontend**
   - Add corpus selection UI
   - Display available corpuses
   - Allow users to switch between corpuses

### Example Integration Code

```python
# In retriever.py
class HybridRetriever:
    def __init__(self, corpus_name: str):
        self.corpus_name = corpus_name
        self.corpus_config = get_registry().get_corpus(corpus_name)
        
        # Initialize corpus-specific ChromaDB and BM25
        self.chroma_client = chromadb.PersistentClient(path=self.corpus_config.chroma_db_path)
        self.chroma_collection = self.chroma_client.get_collection(self.corpus_config.collection_name)
        
        # Load BM25 index
        with open(self.corpus_config.bm25_index_path, 'rb') as f:
            bm25_data = pickle.load(f)
            self.bm25_model = bm25_data['model']
            self.chunk_ids = bm25_data['chunk_ids']
```

## Adding New Corpuses

### Single File Corpus

1. **Add file** to `raw_texts/`
2. **Update jobs.yaml**:
   ```yaml
   new_corpus:
     display_name: "New Corpus"
     description: "Description"
     source_file: "raw_texts/new_corpus.pdf"
     file_type: "pdf"
     is_active: true
   ```
3. **Run ingestion**: `python -m src.embed_retrieve.batch_ingest --corpus new_corpus`

### Multi-File Corpus

1. **Create folder**: `raw_texts/new_corpus/`
2. **Add files** to the folder
3. **Run preprocessing**: `python -m src.embed_retrieve.preprocess_multi_files`
4. **Update jobs.yaml** with the concatenated file
5. **Run ingestion**: `python -m src.embed_retrieve.batch_ingest --corpus new_corpus`

## Maintenance and Troubleshooting

### Checking Corpus Health

```bash
# Check status
python -m src.embed_retrieve.batch_ingest --status-only

# Verify file integrity
ls -la data/processed_chunks/corpus_name/
ls -la data/chroma_db/corpus_name/
ls -la data/bm25_indexes/corpus_name_bm25.pkl
```

### Rebuilding Corrupted Corpuses

```bash
# Force rebuild specific corpus
python -m src.embed_retrieve.batch_ingest --corpus corpus_name --force-rebuild

# Rebuild all corpuses
python -m src.embed_retrieve.batch_ingest --force-rebuild
```

### Backup and Restore

Each corpus is self-contained, making backup/restore simple:
- **Backup**: Copy the entire `data/` directory
- **Restore**: Replace the `data/` directory
- **Selective backup**: Copy specific corpus directories

## Performance Considerations

- **Memory usage**: Each corpus loads its own ChromaDB and BM25 index
- **Disk space**: Each corpus has its own database (~100-500MB per corpus)
- **Switching overhead**: Loading new corpus requires initializing new databases
- **Recommendation**: Implement lazy loading and caching for frequently used corpuses

## Future Enhancements

1. **Corpus Metadata**: Add more metadata (creation date, version, tags)
2. **Corpus Categories**: Group corpuses by type (epics, documentation, etc.)
3. **Corpus Search**: Search across multiple corpuses simultaneously
4. **Corpus Comparison**: Compare content across different corpuses
5. **Incremental Updates**: Update corpuses without full rebuild
6. **Corpus Analytics**: Track usage patterns and performance metrics 