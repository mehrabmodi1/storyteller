# Resilient Build Pipeline

**Date:** 2026-03-30
**Status:** Approved
**Goal:** Fix the corpus embedding build pipeline so it correctly resumes after interruption, respects API rate limits, and never silently skips chunks.

---

## Problems

1. **ChromaDB data loss on interruption:** Individual `upsert` calls don't guarantee disk flush. On `Ctrl+C`, most upserted data is lost. Recovery logic correctly queries ChromaDB for existing IDs, but ChromaDB reports far fewer than were upserted.

2. **Silent chunk skipping on 429:** `_get_embedding` catches rate-limit errors, prints them, returns `[]`. The `if embedding:` check skips the upsert. That chunk is never retried — it's silently lost.

3. **No rate limiting:** The pipeline fires API calls as fast as possible. Gemini free tier allows only 5 RPM for chat (summaries) and 100 RPM for embeddings. Without throttling, most calls hit 429s.

---

## Design

### 1. Rate Limit Configuration (`config/settings.py`)

Add RPM fields to Config. `0` means no throttle.

```python
# Config class
gemini_chat_rpm: int = 5
gemini_embedding_rpm: int = 100
openai_chat_rpm: int = 0
openai_embedding_rpm: int = 0
```

Add resolution properties to Settings:

```python
@property
def chat_rpm(self) -> int:
    return self._config.gemini_chat_rpm if self.provider == "gemini" else self._config.openai_chat_rpm

@property
def embedding_rpm(self) -> int:
    return self._config.gemini_embedding_rpm if self.provider == "gemini" else self._config.openai_embedding_rpm
```

### 2. Rate Limiter (`build_database.py`)

A simple pre-call delay based on RPM:

```python
import time

class _RateLimiter:
    def __init__(self, rpm: int):
        self.min_interval = 60.0 / rpm if rpm > 0 else 0
        self.last_call = 0.0

    def wait(self):
        if self.min_interval == 0:
            return
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()
```

Two instances in `__init__`:
- `self._chat_limiter = _RateLimiter(settings.chat_rpm)`
- `self._embed_limiter = _RateLimiter(settings.embedding_rpm)`

Called before each API call:
- `self._chat_limiter.wait()` before `_get_contextual_summary`
- `self._embed_limiter.wait()` before `_get_embedding`

### 3. Retry on 429 (`build_database.py`)

Both `_get_embedding` and `_get_contextual_summary` retry up to 3 times on 429 errors:

```python
for attempt in range(max_retries):
    try:
        return api_call()
    except Exception as e:
        if '429' in str(e) and attempt < max_retries - 1:
            wait = 20  # default backoff
            print(f"Rate limited. Retrying in {wait}s (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait)
        else:
            raise
```

If all retries fail, the exception propagates and **stops the build**. No silent skipping.

### 4. Batch Upserts (`build_database.py`)

Instead of upserting one chunk at a time, batch in groups of 50:

```python
BATCH_SIZE = 50

for i in range(0, len(to_embed), BATCH_SIZE):
    batch = to_embed[i:i + BATCH_SIZE]

    # Embed each chunk in the batch (rate-limited)
    ids, embeddings, documents, metadatas = [], [], [], []
    for chunk_data in batch:
        self._embed_limiter.wait()
        embedding = self._get_embedding(document_text)
        ids.append(chunk_data['chunk_id'])
        embeddings.append(embedding)
        documents.append(document_text)
        metadatas.append(metadata)

    # Single batch upsert — atomic write to SQLite
    self.chroma_collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    batch_num = (i // BATCH_SIZE) + 1
    total_batches = (len(to_embed) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"Batch {batch_num}/{total_batches} complete. {len(existing_ids) + i + len(batch)} chunks in ChromaDB.")
```

This reduces the number of SQLite commits (one per batch instead of one per chunk) and gives clear progress logging.

### 5. Stop on Failure

If any chunk fails embedding after 3 retries, the build stops with a clear error:

```
FATAL: Failed to embed chunk {chunk_id} after 3 retries.
{total_embedded} chunks successfully embedded. Re-run to resume.
```

On re-run, ChromaDB recovery skips the already-embedded chunks and picks up from the failure point.

---

## Files Changed

| File | Changes |
|---|---|
| `config/settings.py` | Add RPM fields to Config, resolution properties to Settings |
| `embed_retrieve/build_database.py` | Add `_RateLimiter`, retry logic, batch upserts, stop-on-failure |

## Files NOT Changed

- `embed_retrieve/retriever.py` — reads from ChromaDB, no build logic
- `embed_retrieve/config.py` — paths only, no rate limiting
- `services/` — runtime code, not build pipeline
