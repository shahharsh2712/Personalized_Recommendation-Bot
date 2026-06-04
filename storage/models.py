import json
import logging
import numpy as np
from datetime import datetime
from bson.objectid import ObjectId

from .database import Database

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ProductStore:
    """Storage for product data"""

    def __init__(self):
        self.db = Database()

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
            result = self.db.db.products.update_one(
                {"product_id": product_id}, {"$set": doc}, upsert=True
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

    def save_batch(self, products):
        """Save a batch of products"""
        success_count = 0
        for product in products:
            if self.save_product(product):
                success_count += 1

        logger.info(f"Saved {success_count}/{len(products)} products")
        return success_count

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
            cursor = self.db.db.products.find(
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

            # Use MongoDB's $function to calculate cosine similarity
            pipeline = [
                {
                    "$match": {
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

            results = list(self.db.db.products.aggregate(pipeline))
            logger.info(
                f"Found {len(results)} similar products from today's collection"
            )
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

            results = list(self.db.db.products.aggregate(pipeline))
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
            result = self.db.db.products.update_many(
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

    def close(self):
        """Close database connection"""
        self.db.close()


class UserProfileStore:
    """Storage for user profiles"""

    def __init__(self):
        self.db = Database()

    def save_user(self, user):
        """Save a user profile"""
        try:
            # Make sure we have an email
            if "email" not in user:
                logger.error("User missing email field")
                return False

            email = user["email"]

            # Convert embedding from numpy array if needed
            if "embedding" in user and hasattr(user["embedding"], "tolist"):
                user["embedding"] = user["embedding"].tolist()

            # Add last updated timestamp
            user["last_updated"] = datetime.now()

            # Upsert (update if exists, insert if not)
            result = self.db.db.user_profiles.update_one(
                {"email": email}, {"$set": user}, upsert=True
            )

            if result.modified_count > 0:
                logger.info(f"Updated user profile: {email}")
                return True
            elif result.upserted_id:
                logger.info(f"Created new user profile: {email}")
                return True
            else:
                logger.warning(f"User profile unchanged: {email}")
                return True

        except Exception as e:
            logger.error(f"Error saving user {user.get('email', 'unknown')}: {e}")
            return False

    def get_user_by_email(self, email):
        """Get a user by email"""
        try:
            user = self.db.db.user_profiles.find_one({"email": email})
            return user
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None

    def get_active_users(self):
        """Get all active users"""
        try:
            users = list(self.db.db.user_profiles.find({"active": True}))
            logger.info(f"Retrieved {len(users)} active users")
            return users
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
        """Close database connection"""
        self.db.close()


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
