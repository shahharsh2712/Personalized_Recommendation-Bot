import json
import numpy as np
import pickle
from sklearn.metrics.pairwise import cosine_similarity


class SimpleVectorStore:
    def __init__(self):
        self.products = []
        self.embeddings = []

    def add_product(self, product):
        """Add a product and its embedding to the store"""
        if "embedding" in product:
            self.products.append(product)
            self.embeddings.append(product["embedding"])

    def search(self, query_embedding, top_k=5):
        """Search for products similar to the query embedding."""
        if not self.embeddings or not query_embedding:
            return []

        query_dim = len(query_embedding)
        compatible = [
            (i, emb)
            for i, emb in enumerate(self.embeddings)
            if emb and len(emb) == query_dim
        ]
        if not compatible:
            return []

        indices, embeddings = zip(*compatible)
        embeddings_array = np.array(embeddings, dtype=np.float32)
        query_array = np.array(query_embedding, dtype=np.float32)

        similarities = cosine_similarity([query_array], embeddings_array)[0]
        top_local = similarities.argsort()[-top_k:][::-1]

        results = []
        for local_idx in top_local:
            product_idx = indices[local_idx]
            results.append(
                {
                    "product": self.products[product_idx],
                    "similarity": float(similarities[local_idx]),
                }
            )
        return results

    def save(self, filename):
        """Save the vector store to a file"""
        with open(filename, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, filename):
        """Load a vector store from a file"""
        with open(filename, "rb") as f:
            return pickle.load(f)
