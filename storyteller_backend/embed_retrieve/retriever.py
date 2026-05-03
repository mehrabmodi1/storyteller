import chromadb
import pickle
from typing import List, Dict, Optional

from .corpus_registry import get_registry
from .paths import provider_chroma_path
from models.chunk import Chunk
from . import config
from config.settings import settings


class _GeminiEmbeddings:
    """Thin wrapper around google-genai SDK for embeddings."""

    def __init__(self, model: str, api_key: str):
        from google import genai
        self.model = model
        self.client = genai.Client(api_key=api_key)

    def embed_query(self, text: str) -> List[float]:
        from google.genai import types
        result = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
        )
        return result.embeddings[0].values

    def embed_document(self, text: str) -> List[float]:
        from google.genai import types
        result = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
        )
        return result.embeddings[0].values


def _get_embeddings_model():
    """Create an embeddings model for the active provider."""
    if settings.provider == "gemini":
        return _GeminiEmbeddings(
            model=settings.embedding_model,
            api_key=settings.api_key,
        )
    else:
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.api_key,
        )


class HybridRetriever:
    """
    Performs hybrid search by combining results from a keyword-based (BM25)
    and a semantic (ChromaDB) search system using Reciprocal Rank Fusion.
    """

    def __init__(self, corpus_name: Optional[str] = None, api_key: Optional[str] = None):
        self.embeddings = _get_embeddings_model()

        self.corpus_name = corpus_name or "mahabharata"
        self.registry = get_registry()
        self.corpus_config = self.registry.get_corpus(self.corpus_name)

        if not self.corpus_config:
            raise ValueError(f"Corpus '{self.corpus_name}' not found in registry. Available corpuses: {list(self.registry.corpuses.keys())}")

        if not self.corpus_config.is_active:
            raise ValueError(f"Corpus '{self.corpus_name}' is not active.")

        # Load ChromaDB with provider-namespaced path
        chroma_path = provider_chroma_path(self.corpus_config.chroma_db_path)
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.chroma_collection = self.chroma_client.get_collection(name=self.corpus_config.collection_name)

        # Load BM25 Index (shared, not provider-namespaced)
        try:
            with open(self.corpus_config.bm25_index_path, "rb") as f:
                bm25_data = pickle.load(f)
                self.bm25_index = bm25_data['model']
                self.bm25_chunk_ids = bm25_data['chunk_ids']
        except FileNotFoundError:
            raise FileNotFoundError(f"BM25 index not found at {self.corpus_config.bm25_index_path}. Please run the build script first for corpus '{self.corpus_name}'.")

    def _get_query_embedding(self, query: str) -> List[float]:
        try:
            return self.embeddings.embed_query(query)
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            return []

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        if not query:
            return []

        query_embedding = self._get_query_embedding(query)
        semantic_results = self.chroma_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        semantic_ids = semantic_results['ids'][0]

        tokenized_query = query.lower().split(" ")
        bm25_scores = self.bm25_index.get_scores(tokenized_query)

        top_bm25_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k]
        keyword_ids = [self.bm25_chunk_ids[i] for i in top_bm25_indices]

        rrf_k = 60
        fused_scores: Dict[str, float] = {}

        for rank, doc_id in enumerate(semantic_ids):
            if doc_id not in fused_scores:
                fused_scores[doc_id] = 0
            fused_scores[doc_id] += 1 / (rrf_k + rank + 1)

        for rank, doc_id in enumerate(keyword_ids):
            if doc_id not in fused_scores:
                fused_scores[doc_id] = 0
            fused_scores[doc_id] += 1 / (rrf_k + rank + 1)

        reranked_results = sorted(fused_scores.items(), key=lambda item: item[1], reverse=True)

        final_results = []
        top_ids = [doc_id for doc_id, _ in reranked_results[:top_k]]

        if not top_ids:
            return []

        retrieved_docs = self.chroma_collection.get(
            ids=top_ids,
            include=['metadatas', 'documents']
        )

        docs_map: Dict[str, Dict] = {}
        for i, doc_id in enumerate(retrieved_docs['ids']):
            docs_map[doc_id] = {
                "metadata": retrieved_docs['metadatas'][i],
                "document": retrieved_docs['documents'][i]
            }

        for doc_id, score in reranked_results[:top_k]:
            doc_info = docs_map.get(doc_id)
            if doc_info:
                final_results.append({
                    "chunk_id": doc_id,
                    "score": score,
                    "base_text": doc_info['metadata'].get('base_text', 'Base text not found'),
                    "context": doc_info['document'].split('\\n\\nText:')[0].replace('Context: ', ''),
                })

        return final_results 