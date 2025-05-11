import json
import numpy as np
import pickle
from sklearn.metrics.pairwise import cosine_similarity
from vector_store import SimpleVectorStore

# Try importing FAISS, but make it optional
try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("FAISS is not installed. Using slower fallback search method.")
    print("To install FAISS: pip install faiss-cpu")


class ImprovedVectorStore(SimpleVectorStore):
    """Vector store with FAISS acceleration while maintaining compatibility"""

    def __init__(self):
        super().__init__()
        self.index = None
        self.using_faiss = FAISS_AVAILABLE

    def build_index(self):
        """Build a FAISS index for fast similarity search"""
        if not self.embeddings or not FAISS_AVAILABLE:
            return

        # Convert embeddings to the right format
        embeddings_array = np.array(self.embeddings).astype("float32")

        # Create the index - using Inner Product which is equivalent to
        # cosine similarity when vectors are normalized
        dimension = len(self.embeddings[0])
        self.index = faiss.IndexFlatIP(dimension)

        # Normalize vectors for cosine similarity
        faiss.normalize_L2(embeddings_array)

        # Add vectors to index
        self.index.add(embeddings_array)
        print(f"Built FAISS index with {self.index.ntotal} vectors")

    def add_product(self, product):
        """Add a product and its embedding to the store"""
        super().add_product(product)

        # Invalidate index when new products are added
        if self.using_faiss:
            self.index = None

    def add_products(self, products):
        """Add multiple products at once, then build index once"""
        added = 0
        for product in products:
            if "embedding" in product:
                self.products.append(product)
                self.embeddings.append(product["embedding"])
                added += 1

        print(f"Added {added} products to vector store")

        # Build index after adding all products
        if self.using_faiss:
            self.build_index()

    def search(self, query_embedding, top_k=5):
        """Search using FAISS if available, fallback to base implementation"""
        if not self.embeddings:
            return []

        # If FAISS is not available or we have very few products, use base implementation
        if not self.using_faiss or len(self.embeddings) < 100:
            return super().search(query_embedding, top_k)

        # Build/rebuild index if needed
        if self.index is None or self.index.ntotal != len(self.embeddings):
            self.build_index()

        # Normalize query vector for cosine similarity
        query_array = np.array([query_embedding]).astype("float32")
        faiss.normalize_L2(query_array)

        # Search
        scores, indices = self.index.search(query_array, top_k)

        # Return results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:  # FAISS uses -1 for empty slots
                results.append(
                    {"product": self.products[idx], "similarity": float(scores[0][i])}
                )

        return results

    def save(self, filename):
        """Save the vector store to a file"""
        # Temporarily remove the FAISS index before pickling
        # as it's not needed for storage and may cause issues
        temp_index = self.index
        self.index = None

        # Save using the parent method
        super().save(filename)

        # Restore the index
        self.index = temp_index

    @classmethod
    def load(cls, filename):
        """Load a vector store from a file"""
        with open(filename, "rb") as f:
            store = pickle.load(f)

        # Convert SimpleVectorStore to ImprovedVectorStore if needed
        if isinstance(store, SimpleVectorStore) and not isinstance(
            store, ImprovedVectorStore
        ):
            improved_store = ImprovedVectorStore()
            improved_store.products = store.products
            improved_store.embeddings = store.embeddings
            return improved_store

        return store
