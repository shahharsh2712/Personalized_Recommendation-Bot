import os
import json
from datetime import datetime
from storage.models import ProductStore


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    file_path = f"data_store/products_with_embeddings_{today}.json"
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    with open(file_path, "r", encoding="utf-8") as f:
        products = json.load(f)
    store = ProductStore()
    count = 0
    for product in products:
        if store.save_product(product):
            count += 1
    print(f"Imported {count}/{len(products)} products into MongoDB.")
    store.close()


if __name__ == "__main__":
    main()
