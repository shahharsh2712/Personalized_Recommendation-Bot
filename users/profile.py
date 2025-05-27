import os
import logging
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import json

# Import from our modules
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from personalized_recommendations.storage.models import UserProfileStore

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
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.embedding_model = "text-embedding-3-small"
        self.CHIP_EMBEDDINGS = {
            "roles": {
                "Developer": "Software Developer",
                "Indie Hacker": "Indie Hacker",
                "Product Manager": "Product Manager",
                "Marketer": "Digital Marketer",
                "Designer": "UI/UX Designer",
                "Student": "Student",
            },
            "interests": {
                "AI Art": "AI Art and Generation",
                "Productivity": "Productivity Tools",
                "Health": "Health and Wellness",
                "Fin-tech": "Financial Technology",
                "Gaming": "Gaming and Entertainment",
                "Ed-tech": "Educational Technology",
            },
            "platforms": {
                "Web": "Web Browser",
                "macOS": "Apple macOS",
                "Windows": "Microsoft Windows",
                "VS Code": "Visual Studio Code",
                "iOS": "Apple iOS",
                "Android": "Google Android",
            },
        }
        # Initialize embeddings cache
        self._embeddings_cache = {}
        # Load pre-computed embeddings for chips
        self._load_chip_embeddings()

    def _load_chip_embeddings(self):
        """Load pre-computed embeddings for chips from cache or compute them."""
        # Create a cache file path
        cache_file = os.path.join(os.path.dirname(__file__), 'chip_embeddings_cache.json')
        
        # Try to load from cache first
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    self._embeddings_cache = json.load(f)
                logger.info("Loaded chip embeddings from cache")
                return
            except Exception as e:
                logger.warning(f"Failed to load embeddings cache: {e}")

        # If cache doesn't exist or failed to load, compute embeddings
        logger.info("Computing chip embeddings...")
        for category, items in self.CHIP_EMBEDDINGS.items():
            for key, value in items.items():
                if value not in self._embeddings_cache:
                    embedding = self._get_embedding(value)
                    if embedding:
                        self._embeddings_cache[value] = embedding

        # Save to cache
        try:
            with open(cache_file, 'w') as f:
                json.dump(self._embeddings_cache, f)
            logger.info("Saved chip embeddings to cache")
        except Exception as e:
            logger.warning(f"Failed to save embeddings cache: {e}")

    def create_user(self, email, name, preferences=None):
        """Create a new user with the given preferences."""
        if not preferences:
            preferences = {
                "role": None,
                "goal": None,
                "pain_point": None,
                "interests": [],
                "platforms": [],
                "budget_pref": "any",
                "cadence": "daily",
                "channel": "email",
            }
        user = {
            "email": email,
            "name": name,
            "preferences": preferences,
            "embedding": self._calculate_user_vector(preferences),
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow(),
            "subscribed": True,
        }
        return self.store.save_user(user)

    def update_preferences(self, email, preferences):
        """Update user preferences and regenerate embedding."""
        user_vector = self._calculate_user_vector(preferences)
        # Ensure we don't accidentally remove the 'subscribed' field
        user = self.get_user(email)
        subscribed = user.get("subscribed", True) if user else True
        result = self.store.update_user(
            email,
            {
                "$set": {
                    "preferences": preferences,
                    "embedding": user_vector,
                    "last_updated": datetime.utcnow(),
                    "subscribed": subscribed,
                }
            },
        )
        return result.modified_count > 0

    def _calculate_user_vector(self, preferences):
        """Calculate user vector using weighted formula:
        user_vec = 0.35·pain + 0.25·goal + 0.20·role + 0.15·mean(interests) + 0.05·mean(platforms)
        """
        # Initialize components and their weights
        components = {
            'pain_point': (0.35, None),
            'goal': (0.25, None),
            'role': (0.20, None),
            'interests': (0.15, None),
            'platforms': (0.05, None)
        }

        # Get embeddings for each component
        if preferences.get('pain_point'):
            vector = self._get_embedding(preferences['pain_point'])
            if vector is not None:
                components['pain_point'] = (0.35, vector)

        if preferences.get('goal'):
            vector = self._get_embedding(preferences['goal'])
            if vector is not None:
                components['goal'] = (0.25, vector)

        if preferences.get('role'):
            role_text = self.CHIP_EMBEDDINGS['roles'].get(preferences['role'], preferences['role'])
            vector = self._get_embedding(role_text)
            if vector is not None:
                components['role'] = (0.20, vector)

        # Get interest vectors
        if preferences.get('interests'):
            interest_vectors = []
            for interest in preferences['interests']:
                interest_text = self.CHIP_EMBEDDINGS['interests'].get(interest, interest)
                vector = self._get_embedding(interest_text)
                if vector is not None:
                    interest_vectors.append(vector)
            if interest_vectors:
                components['interests'] = (0.15, np.mean(interest_vectors, axis=0))

        # Get platform vectors
        if preferences.get('platforms'):
            platform_vectors = []
            for platform in preferences['platforms']:
                platform_text = self.CHIP_EMBEDDINGS['platforms'].get(platform, platform)
                vector = self._get_embedding(platform_text)
                if vector is not None:
                    platform_vectors.append(vector)
            if platform_vectors:
                components['platforms'] = (0.05, np.mean(platform_vectors, axis=0))

        # Filter out components with no vectors
        valid_components = [(weight, vector) for weight, vector in components.values() if vector is not None]
        
        if not valid_components:
            return None

        # Normalize weights based on available components
        total_weight = sum(weight for weight, _ in valid_components)
        normalized_components = [(weight/total_weight, vector) for weight, vector in valid_components]

        # Calculate weighted sum
        user_vector = np.zeros_like(normalized_components[0][1], dtype=np.float32)
        for weight, vector in normalized_components:
            user_vector += vector * weight

        return user_vector.tolist()

    def _get_embedding(self, text):
        """Generate embedding for a given text"""
        # Check cache first
        if text in self._embeddings_cache:
            # Always convert to numpy array (float32) when returning from cache
            return np.array(self._embeddings_cache[text], dtype=np.float32)

        try:
            response = self.openai_client.embeddings.create(
                input=text, model=self.embedding_model
            )
            embedding = response.data[0].embedding
            # Cache the result
            self._embeddings_cache[text] = embedding
            return np.array(embedding, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

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
