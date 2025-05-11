import json
from improved_vector_store import ImprovedVectorStore


def main():
    # Load merged products with embeddings
    with open("data/merged_products_with_embeddings.json", "r", encoding="utf-8") as f:
        merged_products = json.load(f)

    print(f"Loaded {len(merged_products)} products from merged dataset")

    # Create new improved vector store
    vector_store = ImprovedVectorStore()

    # Add all products at once (more efficient)
    vector_store.add_products(merged_products)

    # Save with a different filename to preserve original
    vector_store.save("data/improved_vector_store.pkl")
    print("Saved improved vector store to data/improved_vector_store.pkl")


if __name__ == "__main__":
    main()
