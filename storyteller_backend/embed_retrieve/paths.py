"""Shared path-resolution helpers for the embedding/retrieval layer.

Both build_database.py (writer) and retriever.py (reader) must resolve the
same on-disk location for a corpus's ChromaDB. Keep that logic here so the
two cannot drift.
"""

from config.settings import settings


def provider_chroma_path(base_path: str) -> str:
    """Return `<base_path>_<provider>` for the active provider.

    `base_path` is the per-corpus base from corpus_registry.json
    (e.g. `data/chroma_db/odyssey`). The provider suffix is read from
    settings at call time so tests can override it.
    """
    return f"{base_path}_{settings.provider}"
