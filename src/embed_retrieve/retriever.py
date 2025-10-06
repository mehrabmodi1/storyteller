import openai
from dotenv import load_dotenv
import os
import chromadb
import pickle
from typing import List, Dict, Optional

from . import config
from .corpus_registry import get_registry
from src.schemas.schemas import Chunk

class HybridRetriever:
    """
    Performs hybrid search by combining results from a keyword-based (BM25)
    and a semantic (ChromaDB) search system using Reciprocal Rank Fusion.
    """

    def __init__(self, corpus_name: Optional[str] = None):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file.")
        
        self.openai_client = openai.OpenAI(api_key=self.api_key)
        
        # Get corpus configuration
        self.corpus_name = corpus_name or "mahabharata"  # Default to mahabharata for backward compatibility
        self.registry = get_registry()
        self.corpus_config = self.registry.get_corpus(self.corpus_name)
        
        if not self.corpus_config:
            raise ValueError(f"Corpus '{self.corpus_name}' not found in registry. Available corpuses: {list(self.registry.corpuses.keys())}")
        
        if not self.corpus_config.is_active:
            raise ValueError(f"Corpus '{self.corpus_name}' is not active.")

        # Load ChromaDB for the specific corpus
        self.chroma_client = chromadb.PersistentClient(path=self.corpus_config.chroma_db_path)
        self.chroma_collection = self.chroma_client.get_collection(name=self.corpus_config.collection_name)

        # Load BM25 Index for the specific corpus
        try:
            with open(self.corpus_config.bm25_index_path, "rb") as f:
                bm25_data = pickle.load(f)
                self.bm25_index = bm25_data['model']
                self.bm25_chunk_ids = bm25_data['chunk_ids']
        except FileNotFoundError:
            raise FileNotFoundError(f"BM25 index not found at {self.corpus_config.bm25_index_path}. Please run the build script first for corpus '{self.corpus_name}'.")

    def _get_query_embedding(self, query: str) -> List[float]:
        try:
            response = self.openai_client.embeddings.create(
                model=config.EMBEDDING_MODEL,
                input=query
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            return []

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Performs a hybrid search and returns a ranked list of results.
        """
        if not query:
            return []

        # 1. Semantic Search (ChromaDB)
        query_embedding = self._get_query_embedding(query)
        semantic_results = self.chroma_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        semantic_ids = semantic_results['ids'][0]

        # 2. Keyword Search (BM25)
        tokenized_query = query.lower().split(" ")
        bm25_scores = self.bm25_index.get_scores(tokenized_query)
        
        # Get top_k results for BM25
        top_bm25_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k]
        keyword_ids = [self.bm25_chunk_ids[i] for i in top_bm25_indices]

        # 3. Reciprocal Rank Fusion (RRF)
        # k is a constant, usually 60, to minimize the impact of high ranks.
        rrf_k = 60
        fused_scores: Dict[str, float] = {}

        # Process semantic results
        for rank, doc_id in enumerate(semantic_ids):
            if doc_id not in fused_scores:
                fused_scores[doc_id] = 0
            fused_scores[doc_id] += 1 / (rrf_k + rank + 1)

        # Process keyword results
        for rank, doc_id in enumerate(keyword_ids):
            if doc_id not in fused_scores:
                fused_scores[doc_id] = 0
            fused_scores[doc_id] += 1 / (rrf_k + rank + 1)
        
        # 4. Sort by fused score
        reranked_results = sorted(fused_scores.items(), key=lambda item: item[1], reverse=True)

        # 5. Fetch full documents for the top results
        final_results = []
        top_ids = [doc_id for doc_id, _ in reranked_results[:top_k]]
        
        if not top_ids:
            return []

        retrieved_docs = self.chroma_collection.get(
            ids=top_ids,
            include=['metadatas', 'documents'] # Explicitly request documents
        )
        
        # Create a mapping for quick lookup of both metadata and documents
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