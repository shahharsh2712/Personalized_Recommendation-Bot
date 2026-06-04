import json
import os
import sys
import time

# Project root for shared embedding provider
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from embeddings.provider import generate_embedding  # noqa: E402


def main():
    with open("data/enriched_products.json", "r", encoding="utf-8") as f:
        products = json.load(f)

    print(f"Loaded {len(products)} enriched products")
    products_with_embeddings = []

    for i, product in enumerate(products):
        print(f"Embedding {i + 1}/{len(products)}: {product['name']}")
        if "embedding_text" in product:
            embedding = generate_embedding(product["embedding_text"])
            if embedding:
                product["embedding"] = embedding
                products_with_embeddings.append(product)
        time.sleep(0.1)

    with open("data/products_with_embeddings.json", "w", encoding="utf-8") as f:
        json.dump(products_with_embeddings, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(products_with_embeddings)} products")


if __name__ == "__main__":
    main()
