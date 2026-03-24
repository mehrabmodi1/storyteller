import sys
import os
import pprint

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from embed_retrieve.retriever import HybridRetriever

def main():
    """
    An interactive script to test the HybridRetriever.
    """
    print("--- Initializing Hybrid Retriever ---")
    try:
        retriever = HybridRetriever()
        print("Retriever initialized successfully.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure you have run the build script to create the necessary database and index files.")
        return

    print("\\n--- Interactive Search ---")
    print("Enter a query to search the Mahabharata. Type 'exit' to end.")

    while True:
        query = input("Query: ")
        if query.lower() == 'exit':
            break
        
        if not query:
            continue

        print(f"Searching for: '{query}'...")
        results = retriever.search(query, top_k=5)
        
        if not results:
            print("No results found.")
        else:
            print("\\n--- Top 5 Hybrid Search Results ---")
            pprint.pprint(results)
            print("-" * 35)

if __name__ == '__main__':
    main() 