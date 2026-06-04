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
from storage.models import ProductStore
from users.profile import UserProfileManager


def reembed_products_from_data_store():
    data_dir = os.path.join(os.path.dirname(__file__), "data_store")
    enriched_files = sorted(
        f
        for f in os.listdir(data_dir)
        if f.startswith("enriched_products_") and f.endswith(".json")
    )
    if not enriched_files:
        print("No enriched_products_*.json files in data_store/")
        return 0

    store = ProductStore()
    total = 0
    today = datetime.now().strftime("%Y-%m-%d")
    output_products = []

    for filename in enriched_files:
        path = os.path.join(data_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            products = json.load(f)

        print(f"Re-embedding {len(products)} products from {filename}...")
        for i, product in enumerate(products):
            text = product.get("embedding_text") or product.get("description", "")
            if not text:
                continue
            embedding = generate_embedding(text)
            if embedding:
                product["embedding"] = embedding
                store.save_product(product)
                output_products.append(product)
                total += 1
            if (i + 1) % 5 == 0:
                print(f"  {i + 1}/{len(products)} done")

    out_path = os.path.join(data_dir, f"products_with_embeddings_{today}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output_products, f, indent=2, ensure_ascii=False)

    store.close()
    print(f"Saved {total} products to MongoDB and {out_path}")
    return total


def reembed_all_users():
    manager = UserProfileManager()
    users = manager.get_active_users()
    count = 0
    for user in users:
        prefs = user.get("preferences") or {}
        if prefs:
            if manager.update_preferences(user["email"], prefs):
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
