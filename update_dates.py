from personalized_recommendations.storage.models import ProductStore


def main():
    store = ProductStore()
    updated = store.update_collection_dates()
    print(f"Updated {updated} products")
    store.close()


if __name__ == "__main__":
    main()
