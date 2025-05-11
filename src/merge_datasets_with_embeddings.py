import json


def merge_datasets_with_embeddings():
    """Merge both datasets that already have embeddings"""
    # Load original products with embeddings
    with open("data/products_with_embeddings.json", "r", encoding="utf-8") as f:
        original_products = json.load(f)

    # Load new popular products with embeddings
    with open("data/popular_products_with_embeddings.json", "r", encoding="utf-8") as f:
        popular_products = json.load(f)

    print(
        f"Loaded {len(original_products)} original products and {len(popular_products)} popular products"
    )

    # Track product IDs to avoid duplicates
    product_ids = set()
    merged_products = []

    # Add all popular products first (they take priority)
    for product in popular_products:
        product_id = product["id"]
        if product_id not in product_ids:
            merged_products.append(product)
            product_ids.add(product_id)

    # Add original products that aren't already included
    duplicates = 0
    for product in original_products:
        product_id = product["id"]
        if product_id not in product_ids:
            merged_products.append(product)
            product_ids.add(product_id)
        else:
            duplicates += 1

    # Save merged dataset
    with open("data/merged_products_with_embeddings.json", "w", encoding="utf-8") as f:
        json.dump(merged_products, f, indent=2, ensure_ascii=False)

    print(f"Created merged dataset with {len(merged_products)} total products")
    print(f"Found {duplicates} duplicate products that were skipped")
    print(
        f"Added {len(merged_products) - len(popular_products)} unique products from original dataset"
    )

    # Count by category
    categories = {}
    for product in merged_products:
        category = product.get("main_category", "Other")
        if category not in categories:
            categories[category] = 0
        categories[category] += 1

    print("\nProducts by Category in Final Dataset:")
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"- {category}: {count}")


if __name__ == "__main__":
    merge_datasets_with_embeddings()
