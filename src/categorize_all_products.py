# src/categorize_all_products.py
import json
from collections import Counter

# Define main product categories and keywords
PRODUCT_CATEGORIES = {
    "Productivity": [
        "productivity",
        "task management",
        "note-taking",
        "calendar",
        "to-do",
        "project management",
        "time tracking",
        "organization",
    ],
    "Communication": [
        "messaging",
        "chat",
        "email",
        "video conferencing",
        "collaboration",
        "team communication",
        "slack",
        "discord",
    ],
    "Design": [
        "design",
        "graphic design",
        "ui design",
        "ux design",
        "prototyping",
        "illustration",
        "creative",
        "photoshop",
        "figma",
    ],
    "Development": [
        "developer tools",
        "programming",
        "coding",
        "software development",
        "development",
        "code",
        "github",
        "devops",
        "web development",
    ],
    "Marketing": [
        "marketing",
        "social media",
        "email marketing",
        "seo",
        "analytics",
        "advertising",
        "growth",
        "campaign",
        "content marketing",
    ],
    "AI Tools": [
        "ai",
        "artificial intelligence",
        "machine learning",
        "chatbot",
        "automation",
        "ml",
        "gpt",
        "llm",
        "neural network",
    ],
    "Business": [
        "business",
        "crm",
        "sales",
        "finance",
        "accounting",
        "invoice",
        "management",
        "enterprise",
        "b2b",
        "saas",
    ],
    "Lifestyle": [
        "health",
        "fitness",
        "wellness",
        "personal",
        "meditation",
        "self-improvement",
        "habit tracking",
        "journal",
    ],
    "Education": [
        "learning",
        "education",
        "course",
        "training",
        "teaching",
        "knowledge",
        "student",
        "school",
        "academy",
    ],
    "Entertainment": [
        "games",
        "entertainment",
        "music",
        "video",
        "streaming",
        "fun",
        "social",
        "media",
    ],
    "Other": [],
}


def categorize_product(product):
    """Categorize a product into one of the main categories"""
    # Combine all product text for analysis with proper None handling
    text = (
        (product.get("name", "") or "")
        + " "
        + (product.get("tagline", "") or "")
        + " "
        + (product.get("description", "") or "")
    ).lower()

    # Check topics
    topics = [t.lower() for t in product.get("topics", []) if t is not None]
    topics_text = " ".join(topics)

    # Check product category
    original_category = (product.get("category", "") or "").lower()

    # Try to find a matching category
    for category, keywords in PRODUCT_CATEGORIES.items():
        if category == "Other":
            continue

        # Check if any keyword matches in text, topics, or category
        if (
            any(keyword in text for keyword in keywords)
            or any(keyword in topics_text for keyword in keywords)
            or any(keyword in original_category for keyword in keywords)
        ):
            return category

    # If no match, return Other
    return "Other"


def categorize_all_products(
    products_file="data/popular_products.json",
    output_file="data/categorized_products.json",
):
    """Categorize all products into main categories"""
    with open(products_file, "r", encoding="utf-8") as f:
        products = json.load(f)

    categorized = {}
    for product in products:
        main_category = categorize_product(product)

        # Add category to product
        product_copy = product.copy()
        product_copy["main_category"] = main_category

        # Add to categorized dictionary
        if main_category not in categorized:
            categorized[main_category] = []
        categorized[main_category].append(product_copy)

    # Flatten for saving
    all_categorized = []
    for category, products in categorized.items():
        all_categorized.extend(products)

    # Save categorized products
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_categorized, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\nProducts by Category:")
    for category, prods in categorized.items():
        print(f"- {category}: {len(prods)} products")

    return categorized


if __name__ == "__main__":
    categorize_all_products()
