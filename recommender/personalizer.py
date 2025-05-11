import os
import logging
import random
from datetime import datetime
import numpy as np
from collections import defaultdict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RecommendationPersonalizer:
    """Advanced personalization for product recommendations"""

    def __init__(self):
        # Personalization settings
        self.diversity_weight = 0.3  # How much to prioritize diversity (0-1)
        self.recency_weight = 0.2  # How much to prioritize recent products
        self.max_category_repeat = 2  # Max number of recommendations from same category

    def personalize_recommendations(
        self, user, candidate_recommendations, user_history=None, max_recommendations=5
    ):
        """
        Apply advanced personalization strategies to candidate recommendations

        Args:
            user: User profile dict
            candidate_recommendations: List of potential recommendations
            user_history: Previous recommendations/interactions (optional)
            max_recommendations: Maximum number of recommendations to return

        Returns:
            List of personalized recommendations
        """
        if not candidate_recommendations:
            logger.warning("No candidate recommendations to personalize")
            return []

        # Apply various personalization strategies
        personalized_recs = self._apply_all_strategies(
            user, candidate_recommendations, user_history
        )

        # Return top N recommendations
        return personalized_recs[:max_recommendations]

    def _apply_all_strategies(self, user, candidates, history):
        """Apply all personalization strategies and re-rank results"""
        # Step 1: Apply contextual boosts (time of day, day of week, etc.)
        candidates_with_context = self._apply_contextual_boosts(candidates)

        # Step 2: Apply diversity to ensure variety
        candidates_with_diversity = self._ensure_diversity(
            user, candidates_with_context
        )

        # Step 3: Avoid repetition from history
        if history:
            candidates_filtered = self._filter_by_history(
                candidates_with_diversity, history
            )
        else:
            candidates_filtered = candidates_with_diversity

        # Step 4: Final sorting and ranking
        return self._final_ranking(candidates_filtered)

    def _apply_contextual_boosts(self, candidates):
        """Boost certain recommendations based on context (time, day, etc.)"""
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()  # 0-6, Monday is 0

        # Copy candidates to avoid modifying originals
        boosted_candidates = []

        for rec in candidates:
            rec_copy = rec.copy()
            boost_factor = 1.0  # Default: no change

            # Time of day boosts
            if 5 <= hour < 9:  # Early morning
                # Boost productivity tools in the morning
                if any(
                    cat in ["Productivity", "Planning", "Email"]
                    for cat in rec.get("categories", [])
                ):
                    boost_factor += 0.15

            elif 9 <= hour < 12:  # Work morning
                # Boost work tools during work hours
                if any(
                    cat in ["Developer Tools", "Business", "Communication"]
                    for cat in rec.get("categories", [])
                ):
                    boost_factor += 0.1

            elif 18 <= hour < 23:  # Evening
                # Boost entertainment/leisure in evening
                if any(
                    cat in ["Entertainment", "Social", "Education"]
                    for cat in rec.get("categories", [])
                ):
                    boost_factor += 0.15

            # Weekend vs Weekday
            if weekday >= 5:  # Weekend (5=Saturday, 6=Sunday)
                # Boost leisure/personal apps on weekend
                if any(
                    cat in ["Entertainment", "Health", "Lifestyle"]
                    for cat in rec.get("categories", [])
                ):
                    boost_factor += 0.2
            else:  # Weekday
                # Boost work tools on weekdays
                if any(
                    cat in ["Productivity", "Business", "Developer Tools"]
                    for cat in rec.get("categories", [])
                ):
                    boost_factor += 0.1

            # Apply boost to confidence score
            original_confidence = rec_copy.get("confidence", 50)
            rec_copy["confidence"] = min(original_confidence * boost_factor, 100)
            rec_copy["original_confidence"] = (
                original_confidence  # Keep original for reference
            )

            boosted_candidates.append(rec_copy)

        return boosted_candidates

    def _ensure_diversity(self, user, candidates):
        """Ensure diversity in recommendations"""
        # If we have too few candidates, return them all
        if len(candidates) <= 3:
            return candidates

        # Group by category
        category_groups = defaultdict(list)
        for rec in candidates:
            # Use first category or "Other" if none
            main_category = rec.get("categories", ["Other"])[0]
            category_groups[main_category].append(rec)

        # Prepare diversified list
        diversified = []

        # First, pick the top item from each category
        # (starting from categories with highest average confidence)
        category_avg_confidence = {}
        for category, items in category_groups.items():
            category_avg_confidence[category] = sum(
                item.get("confidence", 0) for item in items
            ) / len(items)

        # Sort categories by average confidence
        sorted_categories = sorted(
            category_avg_confidence.keys(),
            key=lambda cat: category_avg_confidence[cat],
            reverse=True,
        )

        # Pick top item from each category
        for category in sorted_categories:
            if category_groups[category]:
                # Sort by confidence and take top
                best_item = sorted(
                    category_groups[category],
                    key=lambda x: x.get("confidence", 0),
                    reverse=True,
                )[0]
                diversified.append(best_item)
                category_groups[category].remove(best_item)

        # Fill remaining slots with highest confidence items
        remaining_items = [
            item for sublist in category_groups.values() for item in sublist
        ]
        remaining_items.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        # Combine and sort by confidence
        result = diversified + remaining_items
        result.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        return result

    def _filter_by_history(self, candidates, history):
        """Filter out items that were recently recommended"""
        # Extract product IDs from history
        history_ids = set()
        for hist_item in history:
            if isinstance(hist_item, dict) and "product_id" in hist_item:
                history_ids.add(hist_item["product_id"])

        # Filter candidates
        filtered = [
            rec for rec in candidates if rec.get("product_id") not in history_ids
        ]

        # If we filtered too many, add some back
        if len(filtered) < 3 and len(candidates) > 3:
            # Sort remaining by confidence
            remaining = [
                rec for rec in candidates if rec.get("product_id") in history_ids
            ]
            remaining.sort(key=lambda x: x.get("confidence", 0), reverse=True)

            # Add back highest confidence items
            filtered.extend(remaining[:3])

            # Resort by confidence
            filtered.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        return filtered

    def _final_ranking(self, candidates):
        """Apply final ranking algorithm"""
        # Default sorting by confidence
        return sorted(candidates, key=lambda x: x.get("confidence", 0), reverse=True)

    def add_serendipity(self, recommendations, user, product_store, mix_in_count=1):
        """Add serendipitous (surprising but relevant) recommendations"""
        if not recommendations or len(recommendations) < 2:
            return recommendations

        # Get categories the user doesn't typically prefer
        user_categories = set(
            user.get("preferences", {}).get("preferred_categories", [])
        )

        # Find some products in different categories
        try:
            # Get categories not in user preferences but still somewhat relevant
            all_categories = product_store.get_all_categories()
            other_categories = [
                cat for cat in all_categories if cat not in user_categories
            ]

            if not other_categories:
                return recommendations

            # Select a random category to explore
            explore_category = random.choice(other_categories)

            # Get some products from this category
            serendipity_products = product_store.get_products_by_category(
                explore_category, limit=3
            )

            # Make sure we don't duplicate existing recommendations
            existing_ids = set(rec.get("product_id") for rec in recommendations)
            serendipity_products = [
                p
                for p in serendipity_products
                if p.get("product_id") not in existing_ids
            ]

            if not serendipity_products:
                return recommendations

            # Add serendipity reason
            for product in serendipity_products:
                product["reason"] = f"Something different: explore {explore_category}"
                # Slightly lower confidence for serendipitous recommendations
                product["confidence"] = min(product.get("confidence", 50) * 0.8, 100)

            # Mix in serendipitous products
            # Keep top recommendations, replace last ones with serendipitous
            count = min(
                mix_in_count, len(serendipity_products), len(recommendations) - 1
            )
            if count > 0:
                result = recommendations[:-count] + serendipity_products[:count]
                return result

        except Exception as e:
            logger.error(f"Error adding serendipity: {e}")

        return recommendations


# Example usage
if __name__ == "__main__":
    personalizer = RecommendationPersonalizer()

    # Sample data for testing
    test_recommendations = [
        {
            "product_id": "prod1",
            "name": "TaskMaster Pro",
            "categories": ["Productivity"],
            "confidence": 85,
        },
        {
            "product_id": "prod2",
            "name": "CodeAssist",
            "categories": ["Developer Tools"],
            "confidence": 80,
        },
        {
            "product_id": "prod3",
            "name": "DesignPal",
            "categories": ["Design"],
            "confidence": 75,
        },
        {
            "product_id": "prod4",
            "name": "DevFlow",
            "categories": ["Developer Tools"],
            "confidence": 72,
        },
        {
            "product_id": "prod5",
            "name": "Taskify",
            "categories": ["Productivity"],
            "confidence": 70,
        },
        {
            "product_id": "prod6",
            "name": "MeetingMaster",
            "categories": ["Productivity"],
            "confidence": 68,
        },
    ]

    test_user = {
        "name": "Alex Developer",
        "preferences": {"preferred_categories": ["Developer Tools", "Productivity"]},
    }

    # Test personalization
    personalized = personalizer.personalize_recommendations(
        test_user, test_recommendations, max_recommendations=4
    )

    print("Original recommendations:")
    for rec in test_recommendations:
        print(f"- {rec['name']} ({rec['categories'][0]}): {rec['confidence']}%")

    print("\nPersonalized recommendations:")
    for rec in personalized:
        print(f"- {rec['name']} ({rec['categories'][0]}): {rec['confidence']}%")
