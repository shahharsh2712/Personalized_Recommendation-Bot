import os
import logging
import numpy as np
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import from our modules
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from personalized_recommendations.storage.models import ProductStore, UserProfileStore
from users.profile import UserProfileManager
from personalized_recommendations.recommender.explainer import RecommendationExplainer

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def extract_platforms(product):
    """Extract platform information from various product fields"""
    platforms = set()

    # Check explicit platforms field
    if "platforms" in product:
        platforms.update(product["platforms"])

    # Check category
    if "category" in product:
        category = product["category"].lower()
        if "mac" in category or "apple" in category:
            platforms.add("macos")
        elif "windows" in category:
            platforms.add("windows")
        elif "ios" in category or "iphone" in category:
            platforms.add("ios")
        elif "android" in category:
            platforms.add("android")
        elif "web" in category:
            platforms.add("web")

    # Check topics
    if "topics" in product:
        for topic in product["topics"]:
            topic = topic.lower()
            if "mac" in topic or "apple" in topic:
                platforms.add("macos")
            elif "windows" in topic:
                platforms.add("windows")
            elif "ios" in topic or "iphone" in topic:
                platforms.add("ios")
            elif "android" in topic:
                platforms.add("android")
            elif "web" in topic:
                platforms.add("web")

    # Check description and embedding text
    text_fields = ["embedding_text", "detailed_description", "description"]
    for field in text_fields:
        if field in product:
            text = product[field].lower()
            if "macos" in text or "mac os" in text:
                platforms.add("macos")
            if "windows" in text:
                platforms.add("windows")
            if "ios" in text or "iphone" in text:
                platforms.add("ios")
            if "android" in text:
                platforms.add("android")
            if "web" in text or "browser" in text:
                platforms.add("web")

    return list(platforms)


def extract_price_info(product):
    """Extract price information from product pricing object"""
    if "pricing" not in product:
        return None, None

    pricing = product["pricing"]
    min_price = float("inf")
    max_price = 0

    # Extract prices from tiers
    if "tiers" in pricing:
        for tier in pricing["tiers"]:
            # Look for price patterns like $X.XX, $X/month, etc.
            price_matches = re.findall(r"\$(\d+(?:\.\d+)?)(?:/month)?", tier.lower())
            for price_str in price_matches:
                try:
                    price = float(price_str)
                    min_price = min(min_price, price)
                    max_price = max(max_price, price)
                except ValueError:
                    continue

    # Handle special cases
    if "free" in str(pricing).lower():
        min_price = 0

    if min_price == float("inf"):
        min_price = None
    if max_price == 0:
        max_price = None

    return min_price, max_price


class RecommendationEngine:
    """Engine for generating personalized app recommendations"""

    def __init__(self):
        self.product_store = ProductStore()
        self.user_store = UserProfileStore()
        self.user_manager = UserProfileManager()
        self.explainer = RecommendationExplainer()

    def generate_recommendations_for_user(self, user_email, top_k=5, days=1):
        """Generate recommendations for a specific user using hybrid approach"""
        user = self.user_manager.get_user(user_email)
        if not user:
            logger.error(f"User not found: {user_email}")
            return []
        if "embedding" not in user:
            logger.error(f"User {user_email} has no embedding")
            return []
        user_embedding = user["embedding"]
        preferences = user.get("preferences", {})

        # Determine product pool based on cadence
        cadence = preferences.get("cadence", "daily")
        today = datetime.now().strftime("%Y-%m-%d")
        if cadence == "daily":
            # Only use today's products
            candidate_products = list(
                self.product_store.products.find(
                    {
                        "collection_date": today,
                        "embedding": {"$exists": True, "$ne": []},
                    }
                )
            )
            logger.info(
                f"Using only today's products ({len(candidate_products)}) for daily cadence user {user_email}"
            )
        else:
            # Use previous logic (e.g., last 7 days)
            candidate_products = self.product_store.find_similar_products(
                user_embedding, limit=10
            )
            logger.info(
                f"Using recent products ({len(candidate_products)}) for non-daily cadence user {user_email}"
            )

        # 2. Flexible hard filters with fallback
        filtered_candidates = []
        user_platforms = set(preferences.get("platforms", []))
        user_budget = preferences.get("budget_pref", None)

        # First pass: strict filtering
        for product in candidate_products:
            # Platform filter
            product_platforms = set(extract_platforms(product))
            platform_match = not user_platforms or (user_platforms & product_platforms)

            # Budget filter
            min_price, max_price = extract_price_info(product)
            budget_match = True
            if user_budget == "free-only":
                budget_match = min_price == 0 or min_price is None
            elif user_budget == "freemium-ok":
                budget_match = (
                    min_price == 0
                    or min_price is None
                    or (min_price and min_price <= 10)
                )

            if platform_match and budget_match:
                filtered_candidates.append(product)

        # If no candidates after strict filtering, try relaxed filtering
        if not filtered_candidates:
            for product in candidate_products:
                # Relaxed platform matching
                product_platforms = set(extract_platforms(product))
                platform_match = not user_platforms or any(
                    any(p in up for p in product_platforms) for up in user_platforms
                )

                # Relaxed budget matching
                min_price, max_price = extract_price_info(product)
                budget_match = True
                if user_budget == "free-only":
                    budget_match = min_price is None or min_price <= 5
                elif user_budget == "freemium-ok":
                    budget_match = min_price is None or min_price <= 15

                if platform_match and budget_match:
                    filtered_candidates.append(product)

        # If still no candidates, use original semantic search results
        if not filtered_candidates:
            filtered_candidates = candidate_products[:top_k]
            logger.info(
                "Using unfiltered semantic search results due to no matches after filtering"
            )

        logger.info(
            f"Filtered candidates for {user_email}: {[p['name'] for p in filtered_candidates]}"
        )
        logger.info(f"Passing {len(filtered_candidates)} candidates to LLM for rerank.")

        # 3. LLM rerank and reason generation
        recommendations = self.explainer.batch_llm_rerank_and_reason(
            user, filtered_candidates, top_k=top_k
        )
        logger.info(
            f"LLM/final recommendations for {user_email}: {[r['name'] for r in recommendations]}"
        )

        # Save recommendations
        user_id = str(user["_id"])
        today = datetime.now().strftime("%Y-%m-%d")
        self.user_store.save_recommendation(user_id, recommendations, today)
        return recommendations

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
