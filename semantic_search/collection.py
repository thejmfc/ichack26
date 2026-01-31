import chromadb
import uuid
import os

from chromadb import Settings

from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')


def embed_text(text: str):
    """Generate embeddings using SentenceTransformer"""
    cleaned_text = " ".join(text.split())
    embedding = model.encode(cleaned_text, convert_to_tensor=False)
    return embedding.tolist()

class Collection:
    chroma_client = chromadb.Client(settings=Settings(allow_reset=True))
    collection = None

    def __init__(self):
        try:
            self.collection = self.chroma_client.get_collection(name="docs")
        except Exception as e:
            self.collection = self.chroma_client.create_collection(name="docs")

    def insert(self, id, content):
        try:
            self.collection.upsert(
                ids=[str(id)],
                embeddings=[embed_text(content)],
                documents=[content]
            )
            return True
        except Exception as e:
            print(e)
            return False

    def remove(self, document_id):
        try:
            self.collection.delete(ids=[document_id])
            self.collection = self.chroma_client.create_collection(name="docs")
            return True
        except Exception as e:
            print(e)
            return False
        
        
    def search(self, query, results_count=5):
        try:
            results =  self.collection.query(
            query_embeddings=[embed_text(query)],
            n_results=results_count
            )

            items = [
                {
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                }
                for i in range(len(results["ids"][0]))
            ]

            return items
        except Exception as e:
            print(e)
            return []