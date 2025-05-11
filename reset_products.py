from storage.models import ProductStore
from datetime import datetime


def main():
    store = ProductStore()

    # Delete all existing products
    result = store.db.db.products.delete_many({})
    print(f"Deleted {result.deleted_count} old products")

    # Create index on collection_date
    store.db.db.products.create_index("collection_date")
    print("Created index on collection_date")

    store.close()


if __name__ == "__main__":
    main()
