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
        """Search for products similar to the query embedding"""
        if not self.embeddings:
            return []

        # Convert embeddings to numpy array for efficient computation
        embeddings_array = np.array(self.embeddings)
        query_array = np.array(query_embedding)

        # Calculate cosine similarity
        similarities = cosine_similarity([query_array], embeddings_array)[0]

        # Get indices of top_k most similar products
        top_indices = similarities.argsort()[-top_k:][::-1]

        # Return top_k products with their similarity scores
        results = []
        for idx in top_indices:
            results.append(
                {"product": self.products[idx], "similarity": float(similarities[idx])}
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
