from storage.models import ProductStore
from datetime import datetime


def main():
    store = ProductStore()
    test_product = {
        "id": "test_001",
        "name": "Test Product",
        "tagline": "This is a test product.",
        "description": "Inserted manually to test MongoDB connection.",
        "website": "https://example.com",
        "thumbnail": "",
        "topics": ["Testing"],
        "categories": ["Testing"],
        "votes_count": 0,
        "comments_count": 0,
        "embedding": [0.0] * 1536,
        "enriched": {
            "description": "Test enriched description.",
            "features": ["Test feature 1", "Test feature 2"],
            "use_cases": ["Test use case"],
            "pricing": "Free",
        },
    }
    result = store.save_product(test_product)
    print(f"Inserted test product: {result}")
    store.close()


if __name__ == "__main__":
    main()
