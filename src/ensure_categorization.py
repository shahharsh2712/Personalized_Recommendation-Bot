# src/ensure_categorization.py
import json
from categorize_all_products import categorize_product


def ensure_all_products_categorized():
    """Make sure all products in merged dataset have proper categorization"""
    # Load merged products
    with open("data/merged_enriched_products.json", "r", encoding="utf-8") as f:
        products = json.load(f)

    print(f"Loaded {len(products)} products")

    # Ensure all products have main_category
    updated = 0
    for product in products:
        if "main_category" not in product:
            product["main_category"] = categorize_product(product)
            updated += 1

    print(f"Added missing categories to {updated} products")

    # Save the updated products
    with open("data/final_products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(products)} categorized products to data/final_products.json")

    # Count products by category
    categories = {}
    for product in products:
        category = product["main_category"]
        if category not in categories:
            categories[category] = 0
        categories[category] += 1

    print("\nProducts by Category:")
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"- {category}: {count}")


if __name__ == "__main__":
    ensure_all_products_categorized()
