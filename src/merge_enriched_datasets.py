# src/merge_enriched_datasets.py
import json


def merge_enriched_datasets():
    """Merge both enriched datasets while handling duplicates"""
    # Load original enriched products (500 products)
    with open("data/enriched_products.json", "r", encoding="utf-8") as f:
        original_products = json.load(f)

    # Load newly enriched popular products (1000 products)
    with open("data/enriched_popular_products.json", "r", encoding="utf-8") as f:
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
    with open("data/merged_enriched_products.json", "w", encoding="utf-8") as f:
        json.dump(merged_products, f, indent=2, ensure_ascii=False)

    print(f"Created merged dataset with {len(merged_products)} total products")
    print(f"Found {duplicates} duplicate products that were skipped")
    print(
        f"Added {len(merged_products) - len(popular_products)} unique products from original dataset"
    )


if __name__ == "__main__":
    merge_enriched_datasets()
