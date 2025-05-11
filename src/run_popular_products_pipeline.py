# src/run_popular_products_pipeline.py
import os
import time
from fetch_popular_products import main as fetch_popular
from categorize_all_products import categorize_all_products
from organize_products_by_category import categorize_ai_products


def run_pipeline():
    """Run the complete pipeline for collecting and organizing popular products"""
    print("=== Starting Popular Products Collection Pipeline ===")

    # Step 1: Fetch popular products from ProductHunt
    print("\n1. Fetching popular products...")
    fetch_popular()

    # Step 2: Categorize all products into main categories
    print("\n2. Categorizing products into main categories...")
    categorized = categorize_all_products()

    # Step 3: Further categorize AI products into subcategories
    print("\n3. Categorizing AI products into subcategories...")
    with open("data/categorized_products.json", "r", encoding="utf-8") as f:
        import json

        all_products = json.load(f)

    # Extract AI products
    ai_products = [p for p in all_products if p.get("main_category") == "AI Tools"]

    # Categorize AI products into subcategories
    ai_categorized = categorize_ai_products(ai_products)

    # Print summary of AI subcategories
    print("\nAI Products by Subcategory:")
    for subcategory, products in ai_categorized.items():
        print(f"- {subcategory}: {len(products)} products")

    print("\n=== Pipeline Complete ===")
    print(f"Total products collected: {len(all_products)}")
    print(
        f"AI products categorized: {sum(len(products) for products in ai_categorized.values())}"
    )


if __name__ == "__main__":
    run_pipeline()
