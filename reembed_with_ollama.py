"""
Re-generate product and user embeddings using the configured provider (Ollama).
Run after switching EMBEDDING_PROVIDER=ollama — old OpenAI vectors are incompatible.
"""
import json
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from embeddings.provider import PROVIDER, generate_embedding


def _load_source_products(data_dir):
    """Load the richest products_with_embeddings file, else fall back to enriched."""
    best_products = []
    for prefix in ("products_with_embeddings_", "enriched_products_"):
        for filename in sorted(os.listdir(data_dir), reverse=True):
            if not (filename.startswith(prefix) and filename.endswith(".json")):
                continue
            path = os.path.join(data_dir, filename)
            with open(path, "r", encoding="utf-8") as f:
                products = json.load(f)
            if len(products) > len(best_products):
                best_products = products
        if best_products:
            break

    seen = {}
    for product in best_products:
        product_id = product.get("id") or product.get("product_id")
        if product_id and product_id not in seen:
            seen[product_id] = product
    return list(seen.values())


def _open_product_store():
    try:
        from storage.models import ProductStore

        return ProductStore(), None
    except Exception as e:
        print(f"MongoDB unavailable, skipping DB sync: {e}")
        return None, e


def reembed_products_from_data_store():
    data_dir = os.path.join(os.path.dirname(__file__), "data_store")
    products = _load_source_products(data_dir)
    if not products:
        print("No product files found in data_store/")
        return 0

    store, _ = _open_product_store()
    total = 0
    today = datetime.now().strftime("%Y-%m-%d")
    output_products = []

    print(f"Re-embedding {len(products)} unique products with {PROVIDER}...")
    for i, product in enumerate(products):
        text = product.get("embedding_text") or product.get("description", "")
        if not text:
            continue
        embedding = generate_embedding(text)
        if embedding:
            product["embedding"] = embedding
            if store:
                store.save_product(product)
            output_products.append(product)
            total += 1
        if (i + 1) % 5 == 0:
            print(f"  {i + 1}/{len(products)} done")

    out_path = os.path.join(data_dir, f"products_with_embeddings_{today}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output_products, f, indent=2, ensure_ascii=False)

    if store:
        store.close()
        print(f"Saved {total} products to MongoDB and {out_path}")
    else:
        print(f"Saved {total} products to {out_path} (MongoDB skipped)")
    return total


def reembed_all_users():
    try:
        from users.profile import UserProfileManager
    except Exception as e:
        print(f"Skipping user re-embed: {e}")
        return 0

    try:
        manager = UserProfileManager()
    except Exception as e:
        print(f"MongoDB unavailable, skipping user re-embed: {e}")
        return 0

    users = manager.get_active_users()
    count = 0
    for user in users:
        prefs = user.get("preferences") or {}
        if prefs and manager.update_preferences(user["email"], prefs):
            count += 1
            print(f"Updated embedding for {user['email']}")
    manager.close()
    return count


def rebuild_frontend_vector_store():
    src_dir = os.path.join(os.path.dirname(__file__), "src")
    sys.path.insert(0, src_dir)
    from setup_frontend_data import ensure_vector_store

    pkl = os.path.join(src_dir, "data", "vector_store.pkl")
    if os.path.exists(pkl):
        os.remove(pkl)
    ensure_vector_store()
    print("Rebuilt src/data/vector_store.pkl")


if __name__ == "__main__":
    print(f"Embedding provider: {PROVIDER}")
    reembed_products_from_data_store()
    reembed_all_users()
    rebuild_frontend_vector_store()
    print("Done. Restart run_frontend.py if it is running.")
