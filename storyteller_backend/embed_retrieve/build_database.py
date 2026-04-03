import fitz  # PyMuPDF
import tiktoken
import os
import time
from typing import List, Optional
import chromadb
import json
from tqdm import tqdm
import pickle
from rank_bm25 import BM25Okapi
import argparse

from langchain.chat_models import init_chat_model

from . import config
from models.chunk import Chunk, DocumentPosition
from config.settings import settings


BATCH_SIZE = 50
MAX_RETRIES = 3
DEFAULT_RETRY_WAIT = 20


class _RateLimiter:
    """Pre-call delay to stay within RPM limits."""

    def __init__(self, rpm: int):
        self.min_interval = 60.0 / rpm if rpm > 0 else 0
        self.last_call = time.time()  # First call also waits the full interval

    def wait(self):
        if self.min_interval == 0:
            return
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()


class HybridRetrieverBuilder:
    """
    Builds a hybrid retriever by processing a source text, generating
    contextualized and embedded chunks, and saving them to a persistent
    vector database and a cache.
    """

    def __init__(self, pdf_path: str, api_key: Optional[str] = None):
        self.api_key = settings.resolve_api_key(api_key)
        self.pdf_path = pdf_path

        if settings.provider == "gemini":
            from google import genai
            from google.genai import types
            self._genai_client = genai.Client(api_key=self.api_key)
            self._embed_config = types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
        else:
            from langchain_openai import OpenAIEmbeddings
            self._openai_embeddings = OpenAIEmbeddings(
                model=settings.embedding_model,
                api_key=self.api_key,
            )

        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        chroma_path = config.get_chroma_db_path()
        os.makedirs(chroma_path, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.chroma_collection = self.chroma_client.get_or_create_collection(
            name=config.CHROMA_COLLECTION_NAME
        )

        self._chat_limiter = _RateLimiter(settings.chat_rpm)
        self._embed_limiter = _RateLimiter(settings.embedding_rpm)

        self.tokens: List[int] = []
        self.chunks: List[Chunk] = []

    def _load_and_tokenize_text(self):
        print(f"Loading and tokenizing text from '{self.pdf_path}'...")
        raw_text = ""
        try:
            with fitz.open(self.pdf_path) as doc:
                for page in doc:
                    raw_text += page.get_text()
        except Exception as e:
            print(f"Error reading PDF file: {e}")
            return
        self.tokens = self.tokenizer.encode(raw_text)
        print(f"Successfully tokenized text into {len(self.tokens)} tokens.")

    def _create_initial_chunks(self):
        print("Creating initial text chunks...")
        if not self.tokens:
            print("Token list is empty. Cannot create chunks.")
            return
        step_size = config.CHUNK_SIZE - config.CHUNK_OVERLAP
        for i in range(0, len(self.tokens), step_size):
            chunk_tokens = self.tokens[i:i + config.CHUNK_SIZE]
            if len(chunk_tokens) < config.CHUNK_OVERLAP:
                continue
            chunk_text = self.tokenizer.decode(chunk_tokens)
            position = DocumentPosition(
                start_token_index=i,
                end_token_index=i + len(chunk_tokens)
            )
            self.chunks.append(Chunk(base_text=chunk_text, document_position=position))
        print(f"Created {len(self.chunks)} initial chunks.")

    def _get_contextual_summary(self, chunk: Chunk) -> str:
        start = max(0, chunk.document_position.start_token_index - (config.CONTEXT_WINDOW_SIZE // 2))
        end = min(len(self.tokens), chunk.document_position.end_token_index + (config.CONTEXT_WINDOW_SIZE // 2))
        context_text = self.tokenizer.decode(self.tokens[start:end])

        for attempt in range(MAX_RETRIES):
            self._chat_limiter.wait()
            try:
                llm = init_chat_model(
                    settings.chat_model,
                    model_provider=settings.langchain_chat_provider,
                    api_key=self.api_key,
                    max_tokens=config.CONTEXT_SUMMARY_TOKENS,
                )
                response = llm.invoke([
                    ("system", "You are a helpful assistant. Summarize the following text in about 200 tokens, focusing on the main characters, events, and themes."),
                    ("user", context_text),
                ])
                return response.content or ""
            except Exception as e:
                if '429' in str(e) and attempt < MAX_RETRIES - 1:
                    print(f"  Rate limited (summary). Retrying in {DEFAULT_RETRY_WAIT}s (attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(DEFAULT_RETRY_WAIT)
                else:
                    raise

    def _is_rate_limit_error(self, e: Exception) -> bool:
        """Check if an exception is a rate limit (429) error."""
        error_str = str(e)
        return '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str

    def _parse_retry_delay(self, e: Exception) -> int:
        """Extract retry delay from error message, or return default."""
        error_str = str(e)
        if 'PerDay' in error_str:
            # Daily quota exhausted — no point retrying quickly
            return -1  # Signal: daily limit hit
        # Try to find "retry in Ns" pattern
        import re
        match = re.search(r'retry in (\d+)', error_str, re.IGNORECASE)
        if match:
            return int(match.group(1)) + 5  # Add buffer
        return DEFAULT_RETRY_WAIT

    def _get_embedding(self, text: str) -> List[float]:
        for attempt in range(MAX_RETRIES):
            self._embed_limiter.wait()
            try:
                if settings.provider == "gemini":
                    result = self._genai_client.models.embed_content(
                        model=settings.embedding_model,
                        contents=text,
                        config=self._embed_config,
                    )
                    return result.embeddings[0].values
                else:
                    return self._openai_embeddings.embed_query(text)
            except Exception as e:
                if self._is_rate_limit_error(e):
                    delay = self._parse_retry_delay(e)
                    if delay == -1:
                        print(f"\n  DAILY QUOTA EXHAUSTED. Progress is saved — re-run tomorrow to resume.")
                        raise
                    if attempt < MAX_RETRIES - 1:
                        print(f"  Rate limited (embedding). Retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                        time.sleep(delay)
                    else:
                        raise
                else:
                    raise

    def _load_cached_chunks(self, corpus_name: str) -> list:
        corpus_cache_dir = os.path.join(config.CACHE_DIR, corpus_name)
        if not os.path.isdir(corpus_cache_dir):
            return []
        cached = []
        for filename in os.listdir(corpus_cache_dir):
            if filename.endswith(".json"):
                with open(os.path.join(corpus_cache_dir, filename), 'r') as f:
                    cached.append(json.load(f))
        return cached

    def build(self, corpus_name: str = "mahabharata"):
        """
        Resumable build pipeline:
        1. If cached chunks with summaries exist → load them (skip PDF + summaries)
        2. Otherwise → chunk PDF, generate summaries, save to cache
        3. Skip chunks already in ChromaDB
        4. Embed remaining chunks in batches, upsert to ChromaDB
        5. Stop on failure (no silent skipping)
        """
        # Phase 1: Load or generate chunks with summaries
        cached_chunks = self._load_cached_chunks(corpus_name)

        if cached_chunks:
            print(f"Loaded {len(cached_chunks)} cached chunks for '{corpus_name}' (skipping PDF + summary generation)")
        else:
            print(f"No cached chunks for '{corpus_name}'. Running full pipeline...")
            self._load_and_tokenize_text()
            self._create_initial_chunks()

            corpus_cache_dir = os.path.join(config.CACHE_DIR, corpus_name)
            os.makedirs(corpus_cache_dir, exist_ok=True)

            for chunk in tqdm(self.chunks, desc="Generating summaries"):
                cache_path = os.path.join(corpus_cache_dir, f"{chunk.chunk_id}.json")
                if os.path.exists(cache_path):
                    tqdm.write(f"  Summary cache HIT: {chunk.chunk_id[:8]}")
                else:
                    tqdm.write(f"  Summary cache MISS: {chunk.chunk_id[:8]}... Generating.")
                    chunk.context = self._get_contextual_summary(chunk)
                    with open(cache_path, 'w') as f:
                        json.dump({
                            'chunk_id': chunk.chunk_id,
                            'base_text': chunk.base_text,
                            'context': chunk.context,
                            'document_position': chunk.document_position.model_dump(),
                        }, f, indent=2)

            cached_chunks = self._load_cached_chunks(corpus_name)

        # Phase 2: Embed and upsert in batches (skip chunks already in ChromaDB)
        existing_ids = set(self.chroma_collection.get()['ids'])
        to_embed = [c for c in cached_chunks if c['chunk_id'] not in existing_ids]

        print(f"Total chunks: {len(cached_chunks)}, already in ChromaDB: {len(existing_ids)}, to embed: {len(to_embed)}")

        if not to_embed:
            print("All chunks already embedded. Skipping to BM25.")
        else:
            total_batches = (len(to_embed) + BATCH_SIZE - 1) // BATCH_SIZE
            embedded_count = len(existing_ids)

            with tqdm(total=len(to_embed), desc="Embedding chunks") as pbar:
                for batch_idx in range(0, len(to_embed), BATCH_SIZE):
                    batch = to_embed[batch_idx:batch_idx + BATCH_SIZE]
                    batch_num = (batch_idx // BATCH_SIZE) + 1

                    ids, embeddings, documents, metadatas = [], [], [], []

                    for chunk_data in batch:
                        document_text = f"Context: {chunk_data['context']}\n\nText: {chunk_data['base_text']}"
                        embedding = self._get_embedding(document_text)
                        ids.append(chunk_data['chunk_id'])
                        embeddings.append(embedding)
                        documents.append(document_text)
                        metadatas.append({"base_text": chunk_data['base_text'], **chunk_data.get('document_position', {})})
                        pbar.update(1)

                    # Batch upsert — single atomic write
                    self.chroma_collection.upsert(
                        ids=ids,
                        embeddings=embeddings,
                        documents=documents,
                        metadatas=metadatas,
                    )

                    embedded_count += len(batch)
                    tqdm.write(f"Batch {batch_num}/{total_batches} complete. {embedded_count}/{len(cached_chunks)} chunks in ChromaDB.")

        print("\nVectorDB processing complete.")
        self._build_bm25_index(corpus_name)
        print("Hybrid retriever build process finished.")

    def _build_bm25_index(self, corpus_name: str = "mahabharata"):
        print("Building BM25 index from cached chunks...")
        corpus_cache_dir = os.path.join(config.CACHE_DIR, corpus_name)

        if not os.path.isdir(corpus_cache_dir):
            print(f"Cache directory not found at {corpus_cache_dir}. Aborting.")
            return

        corpus = []
        chunk_ids = []

        cache_files = [f for f in os.listdir(corpus_cache_dir) if f.endswith(".json")]
        if not cache_files:
            print("No cached chunks found to build BM25 index. Aborting.")
            return

        for filename in tqdm(cache_files, desc="Loading chunks for BM25"):
            with open(os.path.join(corpus_cache_dir, filename), 'r') as f:
                data = json.load(f)
                full_text = f"Context: {data.get('context', '')}\n\nText: {data.get('base_text', '')}"
                corpus.append(full_text)
                chunk_ids.append(data['chunk_id'])

        tokenized_corpus = [doc.split(" ") for doc in corpus]
        bm25 = BM25Okapi(tokenized_corpus)

        with open(config.BM25_INDEX_PATH, "wb") as f:
            pickle.dump({"model": bm25, "chunk_ids": chunk_ids}, f)

        print(f"BM25 index built with {len(chunk_ids)} documents and saved to {config.BM25_INDEX_PATH}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Build the hybrid retrieval database.")
    parser.add_argument(
        '--force-rebuild',
        action='store_true',
        help="Force the build process to run even if the BM25 index already exists."
    )
    args = parser.parse_args()

    if os.path.exists(config.BM25_INDEX_PATH) and not args.force_rebuild:
        print("BM25 index already exists. Build process skipped.")
        print(f"To re-run the build, use the --force-rebuild flag.")
    else:
        print("--- Starting Hybrid Retriever Build Process ---")
        builder = HybridRetrieverBuilder(pdf_path=config.PDF_PATH)
        builder.build()
        print("--- Build Process Complete ---")
