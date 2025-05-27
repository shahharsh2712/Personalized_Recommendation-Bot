import os
import logging
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def cleanup_products():
    """Clean up invalid products from MongoDB"""
    try:
        # Connect to MongoDB
        client = MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017/"))
        db = client[os.getenv("MONGODB_DB", "app_recommendations")]
        products = db.products

        # Delete products with null or missing product_id
        result = products.delete_many(
            {
                "$or": [
                    {"product_id": None},
                    {"product_id": ""},
                ]
            }
        )
        logger.info(
            f"Deleted {result.deleted_count} products with null or empty product_id"
        )

        # Delete products with missing required fields
        result = products.delete_many(
            {
                "$or": [
                    {"name": None},
                    {"name": ""},
                    {"description": None},
                    {"description": ""},
                ]
            }
        )
        logger.info(
            f"Deleted {result.deleted_count} products with missing required fields"
        )

        # Get total count after cleanup
        total_count = products.count_documents({})
        logger.info(f"Total products remaining in database: {total_count}")

        # Close connection
        client.close()
        logger.info("MongoDB connection closed")

    except Exception as e:
        logger.error(f"Error cleaning up products: {e}")
        raise


if __name__ == "__main__":
    cleanup_products()
