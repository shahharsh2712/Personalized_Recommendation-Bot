import os

from app_paths import SRC_DATA_DIR
from improved_vector_store import ImprovedVectorStore
from vector_store import SimpleVectorStore


def get_vector_store(use_improved=True, fallback=True):
    """Return a vector store instance from src/data/."""
    improved_path = os.path.join(SRC_DATA_DIR, "improved_vector_store.pkl")
    simple_path = os.path.join(SRC_DATA_DIR, "vector_store.pkl")

    if use_improved and os.path.exists(improved_path):
        try:
            return ImprovedVectorStore.load(improved_path)
        except Exception as e:
            print(f"Error loading improved vector store: {e}")
            if not fallback:
                raise
            print("Falling back to original vector store")

    if os.path.exists(simple_path):
        return SimpleVectorStore.load(simple_path)

    raise FileNotFoundError(
        f"No vector store found in {SRC_DATA_DIR}. Run setup_frontend_data.ensure_vector_store() first."
    )
