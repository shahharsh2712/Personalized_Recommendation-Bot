import json
import os

from app_paths import PROJECT_DATA_STORE, PROJECT_ROOT, SRC_DATA_DIR
from vector_store import SimpleVectorStore


def _load_products_from_data_store():
    """Merge all products_with_embeddings_*.json files from project data_store."""
    if not os.path.isdir(PROJECT_DATA_STORE):
        return []

    products = []
    seen_ids = set()

    for filename in sorted(os.listdir(PROJECT_DATA_STORE)):
        if not (
            filename.startswith("products_with_embeddings_") and filename.endswith(".json")
        ):
            continue

        path = os.path.join(PROJECT_DATA_STORE, filename)
        with open(path, "r", encoding="utf-8") as f:
            batch = json.load(f)

        for product in batch:
            product_id = product.get("id") or product.get("product_id")
            if not product.get("embedding") or product_id in seen_ids:
                continue

            if not product.get("pricing_tier") and isinstance(product.get("pricing"), dict):
                product["pricing_tier"] = product["pricing"].get("model", "")

            products.append(product)
            seen_ids.add(product_id)

    return products


def ensure_vector_store():
    """Build vector store pickle from data_store if missing."""
    os.makedirs(SRC_DATA_DIR, exist_ok=True)

    vector_store_path = os.path.join(SRC_DATA_DIR, "vector_store.pkl")
    merged_path = os.path.join(SRC_DATA_DIR, "merged_products_with_embeddings.json")

    if os.path.exists(vector_store_path):
        return vector_store_path

    products = _load_products_from_data_store()
    if not products:
        raise FileNotFoundError(
            "No products with embeddings found. Add products_with_embeddings_*.json "
            f"to {PROJECT_DATA_STORE} or run the collect pipeline first."
        )

    with open(merged_path, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    store = SimpleVectorStore()
    for product in products:
        store.add_product(product)
    store.save(vector_store_path)

    print(f"Built vector store with {len(products)} products -> {vector_store_path}")
    return vector_store_path
