from storage.models import ProductStore
from datetime import datetime
import json


def main():
    store = ProductStore()
    today = datetime.now().strftime("%Y-%m-%d")

    # Get today's products
    pipeline = [{"$match": {"collection_date": today}}, {"$sort": {"name": 1}}]

    products = list(store.db.db.products.aggregate(pipeline))
    print(f"\nFound {len(products)} products from today ({today}):\n")

    for i, product in enumerate(products, 1):
        print(f"\n{i}. {product.get('name', 'Unknown')}")
        print(f"   Tagline: {product.get('tagline', 'N/A')}")
        print(f"   Website: {product.get('website', 'N/A')}")
        print(f"   Categories: {', '.join(product.get('categories', []))}")
        print(f"   Collection Date: {product.get('collection_date')}")

        # Print enriched data if available
        if "enriched" in product:
            print("\n   Enriched Data:")
            enriched = product["enriched"]
            print(f"   - Description: {enriched.get('description', 'N/A')}")
            print(f"   - Features: {', '.join(enriched.get('features', []))}")
            print(f"   - Use Cases: {', '.join(enriched.get('use_cases', []))}")
            print(f"   - Pricing: {enriched.get('pricing', 'N/A')}")

        # Print embedding info
        if "embedding" in product:
            print(f"\n   Has embedding: Yes (length: {len(product['embedding'])})")
        else:
            print("\n   Has embedding: No")

        print("\n" + "-" * 80)

    store.close()


if __name__ == "__main__":
    main()
