import chromadb
import uuid
import os

from chromadb import Settings
from sympy import true
import generate_embeds

class Collection:
    chroma_client = chromadb.Client(settings=Settings(allow_reset=True))
    collection = None

    def __init__(self):
        try:
            self.collection = self.chroma_client.get_collection(name="docs")
        except Exception as e:
            self.collection = self.chroma_client.create_collection(name="docs")

    def insert(self, content):
        try:
            self.collection.upsert(
                ids=[uuid.uuid4().hex],
                embeddings=[generate_embeds.embed_text(content)],
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
            return self.collection.query(
                query_embeddings=[generate_embeds.embed_text(query)],
                n_results=results_count
            )
        except Exception as e:
            print(e)
            return []