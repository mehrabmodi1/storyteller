import fitz  # PyMuPDF
import tiktoken
import openai
from dotenv import load_dotenv
import os
from typing import List
import chromadb
import json
from tqdm import tqdm
import pickle
from rank_bm25 import BM25Okapi
import argparse

# Assuming config.py is in the same directory
from . import config
from src.schemas.schemas import Chunk, DocumentPosition



class HybridRetrieverBuilder:
    """
    Builds a hybrid retriever by processing a source text, generating
    contextualized and embedded chunks, and saving them to a persistent
    vector database and a cache.
    """

    def __init__(self, pdf_path: str):
        """
        Initializes the builder and sets up the OpenAI client.

        Args:
            pdf_path: The path to the source PDF file.
        """
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file. Please ensure it is set.")
        
        self.openai_client = openai.OpenAI(api_key=self.api_key)
        self.pdf_path = pdf_path
        
        # Use the standard tokenizer for OpenAI's text-embedding models
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(path=config.CHROMA_DB_PATH)
        self.chroma_collection = self.chroma_client.get_or_create_collection(
            name=config.CHROMA_COLLECTION_NAME
        )

        self.tokens: List[int] = []
        self.chunks: List[Chunk] = []

    def _load_and_tokenize_text(self):
        """
        Loads text from the specified PDF file and tokenizes it.
        """
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
        """
        Creates initial chunks from the tokenized text based on the config
        and stores them as Chunk objects.
        """
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
            
            chunk_obj = Chunk(base_text=chunk_text, document_position=position)
            self.chunks.append(chunk_obj)
        
        print(f"Created {len(self.chunks)} initial chunks.")

    def _get_contextual_summary(self, chunk: Chunk) -> str:
        """
        Generates a contextual summary for a chunk using an LLM.
        """
        start = max(0, chunk.document_position.start_token_index - (config.CONTEXT_WINDOW_SIZE // 2))
        end = min(len(self.tokens), chunk.document_position.end_token_index + (config.CONTEXT_WINDOW_SIZE // 2))
        
        context_tokens = self.tokens[start:end]
        context_text = self.tokenizer.decode(context_tokens)

        try:
            response = self.openai_client.chat.completions.create(
                model=config.CONTEXT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Summarize the following text in about 200 tokens, focusing on the main characters, events, and themes."},
                    {"role": "user", "content": context_text}
                ],
                max_tokens=config.CONTEXT_SUMMARY_TOKENS,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"Error generating summary for chunk {chunk.chunk_id}: {e}")
            return ""

    def _get_embedding(self, text: str) -> List[float]:
        """
        Generates an embedding for a given text using an OpenAI embedding model.
        """
        try:
            response = self.openai_client.embeddings.create(
                model=config.EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []

    def build(self):
        """
        Executes the full, resumable pipeline to build the retriever.
        """
        self._load_and_tokenize_text()
        self._create_initial_chunks()

        print(f"Processing {len(self.chunks)} chunks with checkpointing...")

        for chunk in tqdm(self.chunks, desc="Processing Chunks"):
            cache_path = os.path.join(config.CACHE_DIR, f"{chunk.chunk_id}.json")

            if os.path.exists(cache_path):
                # Load from cache
                tqdm.write(f"Cache HIT for chunk ID: {chunk.chunk_id[:8]}...")
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                    chunk.context = data['context']
                    chunk.embedding = data['embedding']
                    chunk.embedding_model = data['embedding_model']
            else:
                # Process and save to cache
                tqdm.write(f"Cache MISS for chunk ID: {chunk.chunk_id[:8]}... Processing now.")
                chunk.context = self._get_contextual_summary(chunk)
                
                document_to_embed = f"Context: {chunk.context}\n\nText: {chunk.base_text}"
                chunk.embedding = self._get_embedding(document_to_embed)
                chunk.embedding_model = config.EMBEDDING_MODEL
                
                with open(cache_path, 'w') as f:
                    json.dump(chunk.model_dump(), f, indent=2)

            # Upsert into ChromaDB
            if chunk.embedding:
                self.chroma_collection.upsert(
                    ids=[chunk.chunk_id],
                    embeddings=[chunk.embedding],
                    documents=[f"Context: {chunk.context}\n\nText: {chunk.base_text}"],
                    metadatas=[{"base_text": chunk.base_text, **chunk.document_position.model_dump()}]
                )
        
        print("\nVectorDB processing complete.")
        self._build_bm25_index()
        print("Hybrid retriever build process finished.")

    def _build_bm25_index(self):
        """
        Builds and saves a BM25 index by loading all processed chunks
        directly from the cache directory.
        """
        print("Building BM25 index from cached chunks...")

        corpus = []
        chunk_ids = []
        
        if not os.path.exists(config.CACHE_DIR):
            print(f"Cache directory not found at {config.CACHE_DIR}. Aborting.")
            return

        cache_files = os.listdir(config.CACHE_DIR)
        if not cache_files:
            print("No cached chunks found to build BM25 index. Aborting.")
            return

        for filename in tqdm(cache_files, desc="Loading chunks for BM25"):
            if filename.endswith(".json"):
                cache_path = os.path.join(config.CACHE_DIR, filename)
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                    full_text = f"Context: {data.get('context', '')}\\n\\nText: {data.get('base_text', '')}"
                    corpus.append(full_text)
                    chunk_ids.append(data['chunk_id'])

        # Tokenize the corpus for BM25
        tokenized_corpus = [doc.split(" ") for doc in corpus]
        bm25 = BM25Okapi(tokenized_corpus)

        # Save the model and the chunk_id mapping
        with open(config.BM25_INDEX_PATH, "wb") as f:
            pickle.dump({"model": bm25, "chunk_ids": chunk_ids}, f)
        
        print(f"BM25 index built with {len(chunk_ids)} documents and saved to {config.BM25_INDEX_PATH}")


if __name__ == '__main__':
    """
    Main execution block to run the full data processing pipeline.
    Includes a check to avoid re-building if the final index already exists.
    """
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


