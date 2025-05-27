import os
import sys
import logging
from datetime import datetime

# Import from our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from personalized_recommendations.storage.models import (
    UserProfileStore,
    RecommendationStore,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def view_recommendations(email, date=None):
    """View recommendations for a user"""
    # Get user profile
    user_store = UserProfileStore()
    rec_store = RecommendationStore()

    user = user_store.get_user_by_email(email)
    if not user:
        logger.error(f"User not found: {email}")
        return False

    user_id = str(user["_id"])
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    # Get recommendations
    recommendations = rec_store.get_user_recommendations(user_id, date)

    if not recommendations:
        print(f"No recommendations found for {email} on {date}")
        user_store.close()
        rec_store.close()
        return False

    # Display recommendations
    print(f"\n=== Personalized App Recommendations for {user['name']} ({email}) ===\n")

    for i, rec in enumerate(recommendations):
        print(f"{i + 1}. {rec['name']} - {rec['tagline']}")
        print(f"   Confidence: {rec['confidence']}%")
        print(f"   Why: {rec['reason']}")
        print(f"   Website: {rec.get('website', 'Not available')}")
        print()

    user_store.close()
    rec_store.close()
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        email = sys.argv[1]
    else:
        email = input("Enter your email: ")

    view_recommendations(email)
