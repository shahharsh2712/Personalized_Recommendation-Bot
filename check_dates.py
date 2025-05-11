from storage.models import ProductStore


def main():
    store = ProductStore()
    store.debug_product_dates()
    store.close()


if __name__ == "__main__":
    main()
