import os
import logging
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import from our modules
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storage.models import ProductStore, UserProfileStore
from users.profile import UserProfileManager

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Engine for generating personalized app recommendations"""

    def __init__(self):
        self.product_store = ProductStore()
        self.user_store = UserProfileStore()
        self.user_manager = UserProfileManager()

    def generate_recommendations_for_user(self, user_email, top_k=5, days=1):
        """Generate recommendations for a specific user"""
        # Get user profile
        user = self.user_manager.get_user(user_email)
        if not user:
            logger.error(f"User not found: {user_email}")
            return []

        preferences = user.get("preferences", {})

        if user.get("embedding"):
            similar_products = self.product_store.find_similar_products(
                user["embedding"], limit=top_k
            )
        else:
            logger.warning(
                f"User {user_email} has no embedding; using preference-based matching"
            )
            similar_products = self._find_products_by_preferences(preferences, top_k)

        if not similar_products:
            logger.error(f"No products found for user: {user_email}")
            return []

        # Format recommendations
        recommendations = self._format_recommendations(user, similar_products)

        # Save recommendations
        user_id = str(user["_id"])
        today = datetime.now().strftime("%Y-%m-%d")
        self.user_store.save_recommendation(user_id, recommendations, today)

        return recommendations

    def _preference_search_terms(self, preferences):
        terms = []
        for key in (
            "interests",
            "preferred_categories",
            "profession",
            "favorite_tools",
            "pain_points",
            "goals",
        ):
            value = preferences.get(key)
            if isinstance(value, list):
                terms.extend(str(v).lower() for v in value if v)
            elif value:
                terms.append(str(value).lower())
        if preferences.get("description"):
            terms.extend(
                w.lower()
                for w in preferences["description"].split()
                if len(w) > 3
            )
        return list(dict.fromkeys(terms))

    def _find_products_by_preferences(self, preferences, limit=5):
        """Match products by profile keywords when OpenAI user embedding is missing."""
        terms = self._preference_search_terms(preferences)
        cursor = self.product_store.db.db.products.find(
            {"embedding": {"$exists": True, "$ne": []}}
        )

        scored = []
        for product in cursor:
            text = " ".join(
                [
                    product.get("name", ""),
                    product.get("tagline", ""),
                    product.get("description", ""),
                    " ".join(product.get("categories", []) or []),
                    " ".join(product.get("topics", []) or []),
                ]
            ).lower()
            if not terms:
                continue
            matches = sum(1 for term in terms if term in text)
            if matches:
                product["similarity"] = matches / len(terms)
                scored.append(product)

        scored.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        if scored:
            return scored[:limit]

        return self.product_store.get_recent_products(days=30, limit=limit)

    def _format_recommendations(self, user, products):
        """Format products as personalized recommendations"""
        recommendations = []
        preferences = user.get("preferences", {})

        for product in products:
            # Calculate confidence (similarity score × 100)
            confidence = min(round(product.get("similarity", 0) * 100, 1), 100)

            # Generate personalized reason
            reason = self._generate_recommendation_reason(preferences, product)

            # Create recommendation object
            recommendation = {
                "product_id": product["product_id"],
                "name": product["name"],
                "tagline": product["tagline"],
                "description": product.get("description", ""),
                "website": product.get("website", ""),
                "thumbnail": product.get("thumbnail", ""),
                "categories": product.get("categories", []),
                "confidence": confidence,
                "reason": reason,
            }

            recommendations.append(recommendation)

        return recommendations

    def _generate_recommendation_reason(self, preferences, product):
        """Generate a personalized reason for this recommendation"""
        reasons = []

        # Check for matching categories
        if "preferred_categories" in preferences:
            user_categories = preferences["preferred_categories"]
            product_categories = product.get("categories", [])

            matching_categories = set(user_categories) & set(product_categories)
            if matching_categories:
                categories_text = ", ".join(list(matching_categories)[:2])
                reasons.append(f"Matches your interest in {categories_text}")

        # Check for matching interests
        if "interests" in preferences:
            user_interests = preferences["interests"]
            product_description = product.get("description", "").lower()
            product_tagline = product.get("tagline", "").lower()

            for interest in user_interests:
                if (
                    interest.lower() in product_description
                    or interest.lower() in product_tagline
                ):
                    reasons.append(f"Related to your interest in {interest}")
                    break

        # Check for profession-related apps
        if "profession" in preferences:
            profession = preferences["profession"].lower()
            product_description = product.get("description", "").lower()

            profession_terms = [profession]
            # Add related terms for common professions
            if profession == "developer" or profession == "software engineer":
                profession_terms.extend(
                    ["code", "programming", "developer", "software"]
                )
            elif profession == "designer":
                profession_terms.extend(["design", "creative", "ui", "ux"])
            elif profession == "marketer":
                profession_terms.extend(
                    ["marketing", "seo", "social media", "audience"]
                )

            for term in profession_terms:
                if term in product_description:
                    reasons.append(
                        f"Helpful for your work as a {preferences['profession']}"
                    )
                    break

        # Default reason based on similarity
        if not reasons:
            reasons.append("Matches your overall preferences")

        return reasons[0]  # Return the first reason

    def generate_daily_recommendations(self):
        """Generate recommendations for all active users"""
        # Get all active users
        active_users = self.user_manager.get_active_users()
        logger.info(f"Found {len(active_users)} active users")

        # Track successful recommendations
        success_count = 0

        # Generate recommendations for each user
        for user in active_users:
            try:
                email = user["email"]
                logger.info(f"Generating recommendations for {email}")

                recommendations = self.generate_recommendations_for_user(email)

                if recommendations:
                    success_count += 1
                    logger.info(
                        f"Generated {len(recommendations)} recommendations for {email}"
                    )
                else:
                    logger.warning(f"No recommendations generated for {email}")

            except Exception as e:
                logger.error(
                    f"Error generating recommendations for {user.get('email', 'unknown')}: {e}"
                )

        logger.info(
            f"Successfully generated recommendations for {success_count}/{len(active_users)} users"
        )
        return success_count

    def close(self):
        """Close all database connections"""
        self.product_store.close()
        self.user_store.close()
        self.user_manager.close()


# Example usage (continued)
if __name__ == "__main__":
    recommendation_engine = RecommendationEngine()

    # Option 1: Generate for a specific user
    test_email = "shahharsh2712@gmail.com"
    user = recommendation_engine.user_manager.get_user(test_email)

    if user:
        print(f"\nGenerating recommendations for: {user['name']} ({test_email})")
        recommendations = recommendation_engine.generate_recommendations_for_user(
            test_email, top_k=5
        )

        print(f"Found {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations):
            print(f"\n{i + 1}. {rec['name']} - {rec['tagline']}")
            print(f"   Confidence: {rec['confidence']}%")
            print(f"   Reason: {rec['reason']}")

    # Option 2: Generate for all active users
    # success_count = recommendation_engine.generate_daily_recommendations()
    # print(f"Generated recommendations for {success_count} users")

    recommendation_engine.close()
