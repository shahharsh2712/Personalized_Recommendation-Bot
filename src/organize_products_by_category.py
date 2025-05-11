import json
import os
import re


def load_products(file_path="data/products.json"):
    """Load products from JSON file"""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def categorize_ai_products(products):
    """Organize products into AI subcategories with more precise matching"""
    # First filter to just AI products
    ai_products = [
        p for p in products if "Artificial Intelligence" in p.get("topics", [])
    ]
    print(f"Found {len(ai_products)} AI products out of {len(products)} total products")

    # Define AI subcategories with more specific keywords
    ai_subcategories = {
        "AI Chatbots": ["chatbot", " chat bot", "chat with", "conversation bot"],
        "AI Content Generation": [
            "content generation",
            "content creator",
            "writing",
            "generate text",
            "text generation",
        ],
        "AI Image Generation": [
            "image generation",
            "create image",
            "generate image",
            "ai art",
            "dall-e",
            "midjourney",
        ],
        "AI Video Generation": ["video generation", "create video", "generate video"],
        "AI Assistants": ["assistant", "ai agent", "personal ai", "virtual assistant"],
        "AI Analytics": [
            "analytics",
            "data analysis",
            "insights",
            "metrics",
            "dashboard",
        ],
        "AI Development": [
            "developer tool",
            "coding",
            "programming",
            "code generation",
            "software development",
        ],
        "AI Productivity": [
            "productivity",
            "workflow",
            "automation",
            "time-saving",
            "efficiency",
        ],
        "AI Marketing": [
            "marketing",
            "ad generation",
            "campaign",
            "social media management",
        ],
        "Other AI": [],
    }

    # Create dictionary to store products by subcategory
    categorized = {subcategory: [] for subcategory in ai_subcategories}
    categorized_products = set()  # Track already categorized products

    # First pass - use more specific matching
    for product in ai_products:
        product_id = product["id"]
        if product_id in categorized_products:
            continue

        # Get product text to analyze
        text = (
            product.get("name", "")
            + " "
            + product.get("tagline", "")
            + " "
            + product.get("description", "")
        ).lower()

        # Check topics too
        topics_text = " ".join(product.get("topics", [])).lower()
        combined_text = text + " " + topics_text

        # Try to find a match with more specific keywords
        assigned = False
        for subcategory, keywords in ai_subcategories.items():
            if subcategory == "Other AI":
                continue

            # Check for specific keyword matches
            if any(keyword in combined_text for keyword in keywords):
                product_copy = product.copy()
                product_copy["ai_subcategory"] = subcategory
                categorized[subcategory].append(product_copy)
                categorized_products.add(product_id)
                assigned = True
                break

    # Check for category-specific conditions
    for product in ai_products:
        product_id = product["id"]
        if product_id in categorized_products:
            continue

        text = (
            product.get("name", "")
            + " "
            + product.get("tagline", "")
            + " "
            + product.get("description", "")
        ).lower()

        category = product.get("category", "").lower()
        topics = [t.lower() for t in product.get("topics", [])]

        # Assign based on explicit category or topic matches
        if "chatbot" in topics or "chat" in category:
            product_copy = product.copy()
            product_copy["ai_subcategory"] = "AI Chatbots"
            categorized["AI Chatbots"].append(product_copy)
            categorized_products.add(product_id)
        elif "content" in topics or "writing" in topics:
            product_copy = product.copy()
            product_copy["ai_subcategory"] = "AI Content Generation"
            categorized["AI Content Generation"].append(product_copy)
            categorized_products.add(product_id)
        elif "image" in topics or "design" in category:
            product_copy = product.copy()
            product_copy["ai_subcategory"] = "AI Image Generation"
            categorized["AI Image Generation"].append(product_copy)
            categorized_products.add(product_id)
        elif "video" in topics:
            product_copy = product.copy()
            product_copy["ai_subcategory"] = "AI Video Generation"
            categorized["AI Video Generation"].append(product_copy)
            categorized_products.add(product_id)
        elif "productivity" in topics or "productivity" in category:
            product_copy = product.copy()
            product_copy["ai_subcategory"] = "AI Productivity"
            categorized["AI Productivity"].append(product_copy)
            categorized_products.add(product_id)
        elif (
            "developer" in topics
            or "development" in topics
            or "software engineering" in category
        ):
            product_copy = product.copy()
            product_copy["ai_subcategory"] = "AI Development"
            categorized["AI Development"].append(product_copy)
            categorized_products.add(product_id)
        elif "marketing" in topics or "marketing" in category:
            product_copy = product.copy()
            product_copy["ai_subcategory"] = "AI Marketing"
            categorized["AI Marketing"].append(product_copy)
            categorized_products.add(product_id)
        elif "analytics" in topics or "data" in topics:
            product_copy = product.copy()
            product_copy["ai_subcategory"] = "AI Analytics"
            categorized["AI Analytics"].append(product_copy)
            categorized_products.add(product_id)

    # Place remaining products in Other AI
    for product in ai_products:
        product_id = product["id"]
        if product_id not in categorized_products:
            product_copy = product.copy()
            product_copy["ai_subcategory"] = "Other AI"
            categorized["Other AI"].append(product_copy)

    return categorized


def save_categorized_products(
    categorized, output_file="data/ai_products_categorized.json"
):
    """Save categorized products to JSON file"""
    # Flatten products list but keep subcategory information
    all_categorized = []
    for subcategory, products in categorized.items():
        all_categorized.extend(products)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_categorized, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(all_categorized)} categorized AI products to {output_file}")


def print_category_summary(categorized):
    """Print summary of products by category"""
    print("\nAI Products by Subcategory:")
    for subcategory, products in categorized.items():
        print(f"- {subcategory}: {len(products)} products")

    # Print sample products from each category
    for subcategory, products in categorized.items():
        if products:
            print(f"\nSample products in {subcategory}:")
            for product in products[:2]:  # Show first 2 products in each category
                print(f"  - {product['name']}: {product['tagline']}")


def main():
    # Load products
    products = load_products()

    # Categorize AI products
    categorized = categorize_ai_products(products)

    # Print summary
    print_category_summary(categorized)

    # Save categorized products
    save_categorized_products(categorized)

    # Identify gaps
    gaps = []
    min_products_per_category = 8
    for category, products in categorized.items():
        if len(products) < min_products_per_category and category != "Other AI":
            gaps.append((category, min_products_per_category - len(products)))

    if gaps:
        print("\nCategories needing more products:")
        for category, needed in gaps:
            print(f"- {category}: Need {needed} more products")


if __name__ == "__main__":
    main()
