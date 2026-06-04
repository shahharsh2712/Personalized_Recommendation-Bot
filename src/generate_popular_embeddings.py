import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from embeddings.provider import generate_embedding  # noqa: E402


def main():
    # Load enriched popular products
    with open("data/enriched_popular_products.json", "r", encoding="utf-8") as f:
        products = json.load(f)

    print(f"Loaded {len(products)} enriched popular products")
    print("Generating embeddings...")

    # Create checkpoint file path
    checkpoint_file = "data/popular_products_embeddings_checkpoint.json"

    # Check if checkpoint exists and load it
    products_with_embeddings = []
    start_index = 0

    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                products_with_embeddings = json.load(f)
            start_index = len(products_with_embeddings)
            print(f"Loaded checkpoint with {start_index} already processed products")
        except Exception as e:
            print(f"Error loading checkpoint: {e}")

    # Process remaining products
    products_to_process = products[start_index:]
    print(f"Remaining products to process: {len(products_to_process)}")

    for i, product in enumerate(products_to_process):
        current_index = start_index + i
        print(
            f"Generating embedding for product {current_index + 1}/{len(products)}: {product['name']}"
        )

        # Generate embedding using the optimized embedding text
        if "embedding_text" in product:
            embedding = generate_embedding(product["embedding_text"])
            if embedding:
                product["embedding"] = embedding
                products_with_embeddings.append(product)
            else:
                print(f"Failed to generate embedding for {product['name']}")
        else:
            print(f"No embedding_text found for {product['name']}")
            # Create basic embedding text as fallback
            fallback_text = (
                f"Product: {product['name']}\nDescription: {product['tagline']}"
            )
            embedding = generate_embedding(fallback_text)
            if embedding:
                product["embedding"] = embedding
                products_with_embeddings.append(product)

        # Save checkpoint every 10 products
        if (current_index + 1) % 10 == 0 or (current_index + 1) == len(products):
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(products_with_embeddings, f, indent=2, ensure_ascii=False)
            print(f"Saved checkpoint with {len(products_with_embeddings)} products")

        # Respect API rate limits
        time.sleep(0.5)

    # Save products with embeddings
    with open("data/popular_products_with_embeddings.json", "w", encoding="utf-8") as f:
        json.dump(products_with_embeddings, f, indent=2, ensure_ascii=False)

    print(
        f"Saved {len(products_with_embeddings)} products with embeddings to data/popular_products_with_embeddings.json"
    )


if __name__ == "__main__":
    main()
