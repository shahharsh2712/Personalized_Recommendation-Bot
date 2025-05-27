import os
import logging
import json
import pymongo
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Database:
    """Database connection for personalized recommendations"""

    def __init__(self):
        # Get MongoDB connection string from environment
        mongo_uri = os.getenv("MONGODB_URI") or "mongodb://localhost:27017/"
        db_name = os.getenv("MONGODB_DB") or "app_recommendations"

        # Debug print
        print(f"[DEBUG] Connecting to MongoDB URI: {mongo_uri}, Database: {db_name}")
        logger.info(
            f"[DEBUG] Connecting to MongoDB URI: {mongo_uri}, Database: {db_name}"
        )

        # Connect to MongoDB
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[db_name]

        # Setup collections
        self.setup_collections()

    def setup_collections(self):
        """Create collections and indexes if they don't exist"""
        # Product collection
        if "products" not in self.db.list_collection_names():
            self.db.create_collection("products")
            self.db.products.create_index("product_id", unique=True)
            self.db.products.create_index("collection_date")
            self.db.products.create_index("categories")
            logger.info("Created products collection with indexes")

        # User profiles collection
        if "user_profiles" not in self.db.list_collection_names():
            self.db.create_collection("user_profiles")
            self.db.user_profiles.create_index("email", unique=True)
            logger.info("Created user_profiles collection with indexes")

        # Recommendations collection
        if "recommendations" not in self.db.list_collection_names():
            self.db.create_collection("recommendations")
            self.db.recommendations.create_index(
                [("user_id", 1), ("date", 1)], unique=True
            )
            logger.info("Created recommendations collection with indexes")

        # Email deliveries collection
        if "email_deliveries" not in self.db.list_collection_names():
            self.db.create_collection("email_deliveries")
            self.db.email_deliveries.create_index(
                [("user_id", 1), ("date", 1)], unique=True
            )
            logger.info("Created email_deliveries collection with indexes")

    def close(self):
        """Close the database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")


# Example usage
if __name__ == "__main__":
    db = Database()
    logger.info("Database connection established")
    db.close()
