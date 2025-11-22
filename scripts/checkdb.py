'''
This script checks the chroma db for the available collections.
'''
import chromadb

chroma_client = chromadb.PersistentClient(path="../data/chroma_db/")
collections = chroma_client.list_collections()

print("Available collections:")

for col in collections:
    print(f"  - {col.name} ({col.count()} documents)")