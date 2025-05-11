from storage.models import ProductStore
from datetime import datetime
import numpy as np


def check_embedding_quality(embedding):
    """Check if embedding is valid and normalized"""
    if not isinstance(embedding, list):
        return False
    if len(embedding) != 1536:  # OpenAI embedding dimension
        return False
    # Check if vector is normalized (length close to 1)
    norm = np.linalg.norm(embedding)
    return 0.99 <= norm <= 1.01


def main():
    store = ProductStore()

    # Get all products (using get_recent_products with a large number to get all)
    products = store.get_recent_products(
        limit=10000
    )  # Using a large number to get all products
    total_products = len(products)

    # Get unique categories
    categories = set()
    for product in products:
        if "category" in product:
            categories.add(product["category"])

    # Get products with embeddings
    products_with_embeddings = [p for p in products if "embedding" in p]

    # Get products with Perplexity enrichment
    products_with_perplexity = [p for p in products if "perplexity_enrichment" in p]

    # Get products with valid embeddings
    products_with_valid_embeddings = [
        p for p in products_with_embeddings if check_embedding_quality(p["embedding"])
    ]

    print("\n=== Product Database Statistics ===")
    print(f"Total products: {total_products}")
    print(f"Products with embeddings: {len(products_with_embeddings)}")
    print(f"Products with valid embeddings: {len(products_with_valid_embeddings)}")
    print(f"Products with Perplexity enrichment: {len(products_with_perplexity)}")
    print(f"Unique categories: {len(categories)}")

    print("\nCategories:")
    for category in sorted(categories):
        count = len([p for p in products if p.get("category") == category])
        print(f"- {category}: {count} products")

    # Check for any products without required fields
    missing_fields = {
        "name": 0,
        "description": 0,
        "category": 0,
        "embedding": 0,
        "perplexity_enrichment": 0,
        "enriched_description": 0,
    }

    for product in products:
        for field in missing_fields:
            if field not in product:
                missing_fields[field] += 1

    print("\nMissing Fields:")
    for field, count in missing_fields.items():
        print(f"- {field}: {count} products missing")

    # Check Perplexity enrichment quality
    if products_with_perplexity:
        print("\nPerplexity Enrichment Quality:")
        enrichment_fields = ["key_features", "use_cases", "technical_specs"]
        for field in enrichment_fields:
            count = len(
                [
                    p
                    for p in products_with_perplexity
                    if field in p["perplexity_enrichment"]
                ]
            )
            print(f"- {field}: {count} products have this field")

    store.close()


if __name__ == "__main__":
    main()
