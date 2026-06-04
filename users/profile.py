import os
import logging
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
# Import from our modules
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from embeddings.provider import generate_embedding
from storage.models import UserProfileStore

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class UserProfileManager:
    """Manages user profiles for personalized recommendations"""

    def __init__(self):
        self.store = UserProfileStore()

    def create_user(self, email, name, preferences=None, active=True):
        """Create a new user profile"""
        if not email or not name:
            logger.error("Email and name are required")
            return False

        # Create user document
        user = {
            "email": email,
            "name": name,
            "preferences": preferences or {},
            "active": active,
            "created_at": datetime.now(),
        }

        # Generate embedding if preferences exist
        if preferences:
            embedding = self._generate_preference_embedding(preferences)
            if embedding is not None:
                user["embedding"] = embedding

        # Save to database
        return self.store.save_user(user)

    def update_preferences(self, email, preferences):
        """Update a user's preferences"""
        # Get existing user
        user = self.store.get_user_by_email(email)
        if not user:
            logger.error(f"User not found: {email}")
            return False

        # Update preferences
        user["preferences"] = preferences

        # Generate new embedding
        embedding = self._generate_preference_embedding(preferences)
        if embedding is not None:
            user["embedding"] = embedding

        # Save updated user
        return self.store.save_user(user)

    def _generate_preference_embedding(self, preferences):
        """Generate embedding for user preferences"""
        # Create text from preferences
        text = self._create_preference_text(preferences)

        embedding = generate_embedding(text)
        if embedding:
            logger.info(f"Generated embedding with {len(embedding)} dimensions")
        else:
            logger.error("Error generating preference embedding")
        return embedding

    def _create_preference_text(self, preferences):
        """Convert preferences to text for embedding"""
        text_parts = []

        # Add interests
        if "interests" in preferences and preferences["interests"]:
            interests = preferences["interests"]
            text_parts.append(f"User is interested in: {', '.join(interests)}")

        # Add preferred categories
        if (
            "preferred_categories" in preferences
            and preferences["preferred_categories"]
        ):
            categories = preferences["preferred_categories"]
            text_parts.append(f"User prefers app categories: {', '.join(categories)}")

        # Add role/profession
        if "profession" in preferences and preferences["profession"]:
            text_parts.append(f"User's profession is: {preferences['profession']}")

        # Add favorite tools
        if "favorite_tools" in preferences and preferences["favorite_tools"]:
            tools = preferences["favorite_tools"]
            text_parts.append(f"User's favorite tools: {', '.join(tools)}")

        # Add goals
        if "goals" in preferences and preferences["goals"]:
            goals = preferences["goals"]
            text_parts.append("User's goals:")
            for goal in goals:
                text_parts.append(f"- {goal}")

        # Add pain points
        if "pain_points" in preferences and preferences["pain_points"]:
            pain_points = preferences["pain_points"]
            text_parts.append("User's pain points:")
            for point in pain_points:
                text_parts.append(f"- {point}")

        # Add free text description
        if "description" in preferences and preferences["description"]:
            text_parts.append(f"Additional information: {preferences['description']}")

        return "\n".join(text_parts)

    def get_user(self, email):
        """Get a user by email"""
        return self.store.get_user_by_email(email)

    def deactivate_user(self, email):
        """Deactivate a user (stop sending recommendations)"""
        user = self.get_user(email)
        if not user:
            logger.error(f"User not found: {email}")
            return False

        user["active"] = False
        return self.store.save_user(user)

    def reactivate_user(self, email):
        """Reactivate a previously deactivated user"""
        user = self.get_user(email)
        if not user:
            logger.error(f"User not found: {email}")
            return False

        user["active"] = True
        return self.store.save_user(user)

    def get_active_users(self):
        """Get all active users"""
        return self.store.get_active_users()

    def close(self):
        """Close the database connection"""
        self.store.close()


# Example usage
if __name__ == "__main__":
    profile_manager = UserProfileManager()

    # Create a test user with preferences
    test_preferences = {
        "interests": ["productivity", "AI tools", "automation"],
        "preferred_categories": ["Productivity", "Artificial Intelligence"],
        "profession": "Software Developer",
        "favorite_tools": ["VS Code", "GitHub", "Notion"],
        "goals": [
            "Finding tools to automate repetitive tasks",
            "Discovering AI tools for code generation",
        ],
        "pain_points": [
            "Too many context switches between tools",
            "Need better code documentation tools",
        ],
        "description": "I'm a full-stack developer working with Node.js and React.",
    }

    profile_manager.create_user(
        "test@example.com", "Test User", preferences=test_preferences
    )

    # Retrieve the user
    user = profile_manager.get_user("test@example.com")
    if user:
        print(
            f"Created user: {user['name']} with embedding dimensions: {len(user['embedding']) if 'embedding' in user else 'none'}"
        )

    profile_manager.close()
