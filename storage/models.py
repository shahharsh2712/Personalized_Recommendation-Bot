import json
import logging
import numpy as np
from datetime import datetime, timedelta
from bson.objectid import ObjectId
import os
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv

from .database import Database

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("personalized_recommendations/logs/storage.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class ProductStore:
    """MongoDB store for products"""

    def __init__(self):
        """Initialize MongoDB connection"""
        try:
            self.client = MongoClient(os.getenv("MONGODB_URI"))
            self.db = self.client[os.getenv("MONGODB_DB", "product_recommendations")]
            self.products = self.db.products
            logger.info("Successfully connected to MongoDB")
        except PyMongoError as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def close(self):
        """Close MongoDB connection"""
        try:
            self.client.close()
            logger.info("MongoDB connection closed")
        except PyMongoError as e:
            logger.error(f"Error closing MongoDB connection: {e}")

    def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all products from MongoDB"""
        try:
            products = list(self.products.find())
            logger.info(f"Retrieved {len(products)} products from MongoDB")
            return products
        except PyMongoError as e:
            logger.error(f"Error retrieving products from MongoDB: {e}")
            return []

    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get a product by ID from MongoDB"""
        try:
            product = self.products.find_one({"product_id": product_id})
            if product:
                logger.info(f"Retrieved product {product_id} from MongoDB")
            else:
                logger.warning(f"Product {product_id} not found in MongoDB")
            return product
        except Exception as e:
            logger.error(f"Error retrieving product {product_id} from MongoDB: {e}")
            return None

    def save_batch(self, products: list) -> int:
        """Save a batch of products to MongoDB. Returns the number of successfully saved products."""
        if not products:
            logger.warning("No products to save.")
            return 0
        now = datetime.utcnow()
        success_count = 0
        for product in products:
            # Ensure product_id is present
            product_id = product.get("product_id") or product.get("id")
            if not product_id:
                logger.warning(f"Skipping product with missing product_id: {product}")
                continue
            product["product_id"] = str(product_id)
            product["id"] = str(product_id)  # for backward compatibility
            product["updated_at"] = now
            if "created_at" not in product:
                product["created_at"] = now
            # Ensure top-level collection_date
            collection_date = None
            if "collection_date" in product:
                collection_date = product["collection_date"]
            elif "data_sources" in product and isinstance(
                product["data_sources"], dict
            ):
                collection_date = product["data_sources"].get("collection_date")
            if not collection_date:
                collection_date = datetime.now().strftime("%Y-%m-%d")
            product["collection_date"] = collection_date
            # Validate required fields
            if not product.get("name") or not product.get("description"):
                logger.warning(
                    f"Skipping product with missing name/description: {product}"
                )
                continue
            try:
                result = self.products.update_one(
                    {"product_id": product["product_id"]},
                    {"$set": product},
                    upsert=True,
                )
                if result.upserted_id or result.modified_count > 0:
                    success_count += 1
            except Exception as e:
                logger.error(f"Error saving product {product_id}: {e}")
        logger.info(f"Saved {success_count} products to MongoDB.")
        return success_count

    def _validate_product(self, product: Dict[str, Any]) -> bool:
        """Validate a product has all required fields"""
        required_fields = ["id", "name", "description"]
        return all(field in product for field in required_fields)

    def delete_product(self, product_id: str) -> bool:
        """Delete a product from MongoDB"""
        try:
            result = self.products.delete_one({"product_id": product_id})
            if result.deleted_count > 0:
                logger.info(f"Deleted product {product_id} from MongoDB")
                return True
            else:
                logger.warning(f"Product {product_id} not found in MongoDB")
                return False
        except Exception as e:
            logger.error(f"Error deleting product {product_id} from MongoDB: {e}")
            return False

    def delete_all_products(self) -> int:
        """Delete all products from MongoDB"""
        try:
            result = self.products.delete_many({})
            count = result.deleted_count
            logger.info(f"Deleted {count} products from MongoDB")
            return count
        except PyMongoError as e:
            logger.error(f"Error deleting all products from MongoDB: {e}")
            return 0

    def save_product(self, product):
        """Save a product to the database"""
        print(
            f"[DEBUG] Attempting to save product: {product.get('name')} ({product.get('id')})"
        )
        try:
            # Make sure we have a product_id
            if "id" not in product:
                logger.error("Product missing id field")
                return False

            product_id = product["id"]

            # Convert embedding from numpy array if needed
            if "embedding" in product and hasattr(product["embedding"], "tolist"):
                product["embedding"] = product["embedding"].tolist()

            # Create document for storage
            doc = {
                "product_id": product_id,
                "name": product.get("name", ""),
                "tagline": product.get("tagline", ""),
                "description": product.get("description", ""),
                "website": product.get("website", ""),
                "thumbnail": product.get("thumbnail", ""),
                "topics": product.get("topics", []),
                "categories": product.get("categories", []),
                "collection_date": datetime.now().strftime("%Y-%m-%d"),
                "votes_count": product.get("votes_count", 0),
                "comments_count": product.get("comments_count", 0),
                "last_updated": datetime.now(),
            }

            # Add enriched data if available
            if "enriched" in product:
                doc["enriched"] = product["enriched"]

            # Add embedding if available
            if "embedding" in product:
                doc["embedding"] = product["embedding"]

            # Upsert (update if exists, insert if not)
            result = self.products.update_one(
                {"id": product_id}, {"$set": doc}, upsert=True
            )

            if result.modified_count > 0:
                logger.info(f"Updated product: {product.get('name')}")
                return True
            elif result.upserted_id:
                logger.info(f"Inserted new product: {product.get('name')}")
                return True
            else:
                logger.warning(f"Product unchanged: {product.get('name')}")
                return True

        except Exception as e:
            logger.error(f"Error saving product {product.get('name', 'unknown')}: {e}")
            return False

    def get_recent_products(self, days=1, limit=20):
        """Get products from the last X days"""
        try:
            # Calculate date threshold
            if days <= 0:
                days = 1

            from datetime import datetime, timedelta

            threshold_date = (datetime.now() - timedelta(days=days)).strftime(
                "%Y-%m-%d"
            )

            # Query for recent products
            cursor = self.products.find(
                {"collection_date": {"$gte": threshold_date}},
                sort=[("collection_date", -1)],
                limit=limit,
            )

            products = list(cursor)
            logger.info(f"Retrieved {len(products)} products from the last {days} days")
            return products

        except Exception as e:
            logger.error(f"Error getting recent products: {e}")
            return []

    def find_similar_products(self, embedding, limit=10):
        """Find products similar to the given embedding"""
        if not embedding:
            return []

        try:
            # Convert embedding to list if it's numpy array
            if hasattr(embedding, "tolist"):
                embedding = embedding.tolist()

            # Get date range (last 7 days)
            today = datetime.now()
            seven_days_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            today_str = today.strftime("%Y-%m-%d")

            # Use MongoDB's $function to calculate cosine similarity
            pipeline = [
                # Match products from last 7 days
                {
                    "$match": {
                        "collection_date": {"$gte": seven_days_ago, "$lte": today_str},
                        "embedding": {"$exists": True, "$ne": []},
                    }
                },
                {
                    "$addFields": {
                        "similarity": {
                            "$function": {
                                "body": """
                                function(embedding, queryEmbedding) {
                                    if (!embedding || !queryEmbedding || embedding.length != queryEmbedding.length) {
                                        return 0;
                                    }
                                    
                                    let dotProduct = 0;
                                    let normA = 0;
                                    let normB = 0;
                                    for (let i = 0; i < embedding.length; i++) {
                                        dotProduct += embedding[i] * queryEmbedding[i];
                                        normA += embedding[i] * embedding[i];
                                        normB += queryEmbedding[i] * queryEmbedding[i];
                                    }
                                    if (normA <= 0 || normB <= 0) {
                                        return 0;
                                    }
                                    return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
                                }
                                """,
                                "args": ["$embedding", embedding],
                                "lang": "js",
                            }
                        }
                    }
                },
                {"$sort": {"similarity": -1}},
                {"$limit": limit},
            ]

            results = list(self.products.aggregate(pipeline))
            logger.info(f"Found {len(results)} similar products from the last 7 days")
            return results

        except Exception as e:
            logger.error(f"Error finding similar products: {e}")
            return []

    def debug_product_dates(self):
        """Debug method to check product collection dates"""
        try:
            # Get all products with their collection dates
            pipeline = [
                {"$project": {"name": 1, "collection_date": 1, "_id": 0}},
                {"$sort": {"collection_date": -1}},
            ]

            results = list(self.products.aggregate(pipeline))
            logger.info(f"Found {len(results)} products with dates:")
            for product in results:
                logger.info(
                    f"Product: {product.get('name')}, Date: {product.get('collection_date')}"
                )

            return results
        except Exception as e:
            logger.error(f"Error checking product dates: {e}")
            return []

    def update_collection_dates(self):
        """Update collection dates for products collected today"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")

            # Update all products that have embeddings but no collection date
            result = self.products.update_many(
                {
                    "embedding": {"$exists": True, "$ne": []},
                    "$or": [
                        {"collection_date": {"$exists": False}},
                        {"collection_date": "2025-04-15"},  # Update old test data
                    ],
                },
                {"$set": {"collection_date": today}},
            )

            logger.info(
                f"Updated collection dates for {result.modified_count} products to {today}"
            )
            return result.modified_count

        except Exception as e:
            logger.error(f"Error updating collection dates: {e}")
            return 0


class UserProfileStore:
    """Storage for user profiles"""

    def __init__(self):
        self.client = MongoClient(
            os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        )
        self.db = self.client[os.getenv("MONGODB_DB", "app_recommendations")]
        self.users = self.db.users

    def save_user(self, user):
        """Save or update a user in the database"""
        try:
            result = self.users.update_one(
                {"email": user["email"]}, {"$set": user}, upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error saving user: {e}")
            return False

    def update_user(self, email, update_data):
        """Update a user's data in the database"""
        try:
            result = self.users.update_one({"email": email}, update_data)
            return result
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return None

    def get_user_by_email(self, email):
        """Get a user by email"""
        try:
            return self.users.find_one({"email": email})
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None

    def get_active_users(self):
        """Get all active users (now defined as subscribed: true)"""
        try:
            return list(self.users.find({"subscribed": True}))
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []

    def save_recommendation(self, user_id, recommendations, date=None):
        """Save recommendations for a user"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        try:
            # Create recommendation document
            doc = {
                "user_id": user_id,
                "date": date,
                "recommendations": recommendations,
                "created_at": datetime.now(),
            }

            # Upsert (update if exists, insert if not)
            result = self.db.db.recommendations.update_one(
                {"user_id": user_id, "date": date}, {"$set": doc}, upsert=True
            )

            if result.modified_count > 0 or result.upserted_id:
                logger.info(f"Saved recommendations for user {user_id} on {date}")
                return True
            else:
                logger.warning(
                    f"Recommendations unchanged for user {user_id} on {date}"
                )
                return True

        except Exception as e:
            logger.error(f"Error saving recommendations for user {user_id}: {e}")
            return False

    def get_user_recommendations(self, user_id, date=None):
        """Get recommendations for a user"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        try:
            doc = self.db.db.recommendations.find_one(
                {"user_id": user_id, "date": date}
            )
            if doc:
                return doc["recommendations"]
            return []
        except Exception as e:
            logger.error(f"Error getting recommendations for user {user_id}: {e}")
            return []

    def log_email_delivery(self, user_id, email, subject, date=None):
        """Log an email delivery"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        try:
            # Create delivery document
            doc = {
                "user_id": user_id,
                "email": email,
                "subject": subject,
                "date": date,
                "sent_at": datetime.now(),
            }

            # Insert delivery record
            result = self.db.db.email_deliveries.insert_one(doc)

            if result.inserted_id:
                logger.info(f"Logged email delivery to {email} on {date}")
                return True
            else:
                logger.warning(f"Failed to log email delivery to {email}")
                return False

        except Exception as e:
            logger.error(f"Error logging email delivery to {email}: {e}")
            return False

    def close(self):
        """Close the database connection"""
        self.client.close()


class RecommendationStore:
    """Dedicated store for recommendations"""

    def __init__(self):
        self.db = Database()
        self.user_store = UserProfileStore()

    def save_user_recommendations(self, user_id, recommendations, date=None):
        """Save recommendations for a user"""
        return self.user_store.save_recommendation(user_id, recommendations, date)

    def get_user_recommendations(self, user_id, date=None):
        """Get recommendations for a user"""
        return self.user_store.get_user_recommendations(user_id, date)

    def log_email_delivery(self, user_id, email, subject, date=None):
        """Log an email delivery"""
        return self.user_store.log_email_delivery(user_id, email, subject, date)

    def close(self):
        """Close database connection"""
        self.db.close()


# Example usage
if __name__ == "__main__":
    # Test product store
    product_store = ProductStore()

    # Create a test product
    test_product = {
        "id": "test-product-123",
        "name": "Test Product",
        "tagline": "A test product for storage",
        "description": "This is a test product to verify storage functionality",
        "website": "https://example.com",
        "thumbnail": "https://example.com/image.jpg",
        "topics": ["Test", "Example"],
        "categories": ["Tools", "Testing"],
        "votes_count": 42,
        "comments_count": 7,
        "data_sources": {"collection_date": datetime.now().strftime("%Y-%m-%d")},
        "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
    }

    # Save the test product
    product_store.save_product(test_product)

    # Get recent products
    recent = product_store.get_recent_products(days=1, limit=5)
    print(f"Found {len(recent)} recent products")

    # Close the store
    product_store.close()
