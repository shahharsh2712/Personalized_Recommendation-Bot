import json
from collections import Counter


def analyze_product_dataset(file_path="data/products.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    # General statistics
    total_products = len(products)
    categories = Counter([p["category"] for p in products])

    # AI-specific analysis
    ai_products = [
        p for p in products if "Artificial Intelligence" in p.get("topics", [])
    ]
    ai_categories = Counter([p["category"] for p in ai_products])

    # Find additional topics frequently associated with AI
    ai_related_topics = Counter()
    for p in ai_products:
        for topic in p.get("topics", []):
            if topic != "Artificial Intelligence":
                ai_related_topics[topic] += 1

    # Print report
    print(f"Total products: {total_products}")
    print(
        f"Total AI products: {len(ai_products)} ({len(ai_products) / total_products * 100:.1f}%)"
    )

    print("\nTop 10 Categories:")
    for cat, count in categories.most_common(10):
        print(f"- {cat}: {count} products")

    print("\nAI Products by Primary Category:")
    for cat, count in ai_categories.most_common():
        print(f"- {cat}: {count} products")

    print("\nTop Topics Associated with AI Products:")
    for topic, count in ai_related_topics.most_common(15):
        print(f"- {topic}: {count} products")

    # Return data for further processing
    return products, ai_products, ai_categories, ai_related_topics


if __name__ == "__main__":
    analyze_product_dataset()
