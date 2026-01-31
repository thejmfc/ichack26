"""semantic_search package

Keep __init__ lightweight so importing the package doesn't require heavy
third-party dependencies (e.g. chromadb or sentence-transformers).
Import submodules explicitly where needed: `from semantic_search import collection`.
"""

__all__ = ["collection", "embeddings", "generate_embeds"]
