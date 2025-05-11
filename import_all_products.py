import os
import json
from storage.models import ProductStore


def main():
    data_dir = "data_store"
    files = [
        f
        for f in os.listdir(data_dir)
        if f.startswith("products_with_embeddings_") and f.endswith(".json")
    ]
    if not files:
        print("No products_with_embeddings_*.json files found in data_store.")
        return
    store = ProductStore()
    total = 0
    for file in sorted(files):
        file_path = os.path.join(data_dir, file)
        with open(file_path, "r", encoding="utf-8") as f:
            products = json.load(f)
        count = 0
        for product in products:
            if store.save_product(product):
                count += 1
        print(f"Imported {count}/{len(products)} products from {file} into MongoDB.")
        total += count
    store.close()
    print(f"Total imported: {total} products.")


if __name__ == "__main__":
    main()
