import os
from vector_store import SimpleVectorStore
from improved_vector_store import ImprovedVectorStore


def get_vector_store(use_improved=True, fallback=True):
    """Factory function to get the appropriate vector store

    Args:
        use_improved: Whether to try using the improved store
        fallback: Whether to fall back to the original if improved is not available

    Returns:
        A vector store instance
    """
    if use_improved:
        # Try to load improved store
        if os.path.exists("data/improved_vector_store.pkl"):
            try:
                return ImprovedVectorStore.load("data/improved_vector_store.pkl")
            except Exception as e:
                print(f"Error loading improved vector store: {e}")
                if not fallback:
                    raise
                print("Falling back to original vector store")
        elif not fallback:
            raise FileNotFoundError("Improved vector store not found")

    # Fall back to original store
    if os.path.exists("data/vector_store.pkl"):
        return SimpleVectorStore.load("data/vector_store.pkl")

    raise FileNotFoundError("No vector store found")
