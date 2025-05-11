import json
from vector_store import SimpleVectorStore


def main():
    # Load products with embeddings
    with open("data/products_with_embeddings.json", "r", encoding="utf-8") as f:
        products = json.load(f)

    print(f"Loaded {len(products)} products with embeddings")

    # Create vector store
    vector_store = SimpleVectorStore()

    # Add products to vector store
    for product in products:
        vector_store.add_product(product)

    print(f"Added {len(vector_store.products)} products to vector store")

    # Save vector store
    vector_store.save("data/vector_store.pkl")
    print("Saved vector store to data/vector_store.pkl")


if __name__ == "__main__":
    main()
