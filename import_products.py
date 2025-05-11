import os
import sys
import json
import logging
from datetime import datetime

# Import from our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from storage.models import ProductStore

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def import_products_from_file(file_path):
    """Import products from a JSON file into MongoDB"""
    # Check if file exists
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return 0

    # Read products from file
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            products = json.load(f)

        logger.info(f"Loaded {len(products)} products from {file_path}")
    except Exception as e:
        logger.error(f"Error reading products file: {e}")
        return 0

    # Save products to database
    product_store = ProductStore()
    count = 0

    for product in products:
        try:
            if product_store.save_product(product):
                count += 1
        except Exception as e:
            logger.error(f"Error saving product {product.get('name', 'unknown')}: {e}")

    logger.info(f"Imported {count}/{len(products)} products into database")
    product_store.close()

    return count


def main():
    """Main entry point"""
    # Find all product files in data_store directory
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_store")

    if not os.path.exists(data_dir):
        logger.error(f"Data directory not found: {data_dir}")
        return 1

    # Find embedding files
    embedding_files = []
    for file in os.listdir(data_dir):
        if file.startswith("products_with_embeddings_") and file.endswith(".json"):
            embedding_files.append(os.path.join(data_dir, file))

    if not embedding_files:
        logger.error("No product embedding files found in data_store directory")
        return 1

    # Sort by date (most recent first)
    embedding_files.sort(reverse=True)

    # Import from each file
    total_count = 0
    for file_path in embedding_files:
        count = import_products_from_file(file_path)
        total_count += count

    logger.info(f"Total products imported: {total_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
