import os
import sys
import logging
from datetime import datetime

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from users.profile import UserProfileManager

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class UserOnboarding:
    """User-friendly onboarding interface"""

    def __init__(self):
        self.profile_manager = UserProfileManager()

    def onboard_user_interactive(self):
        """Interactive console-based onboarding process"""
        print("\n===== New User Onboarding =====\n")

        # Collect basic information
        name = input("Enter user's full name: ")
        email = input("Enter user's email address: ")

        # Collect preferences
        print("\nLet's collect some preferences to personalize recommendations...")
        preferences = {}

        # Interests
        interests_input = input("Enter interests (comma-separated): ")
        if interests_input.strip():
            preferences["interests"] = [
                interest.strip() for interest in interests_input.split(",")
            ]

        # Categories
        categories_input = input("Enter preferred app categories (comma-separated): ")
        if categories_input.strip():
            preferences["preferred_categories"] = [
                category.strip() for category in categories_input.split(",")
            ]

        # Profession
        profession = input("Enter profession or role: ")
        if profession.strip():
            preferences["profession"] = profession

        # Favorite tools
        tools_input = input("Enter favorite tools (comma-separated): ")
        if tools_input.strip():
            preferences["favorite_tools"] = [
                tool.strip() for tool in tools_input.split(",")
            ]

        # Goals
        print("Enter goals (enter empty line when done):")
        goals = []
        while True:
            goal = input("- ")
            if not goal.strip():
                break
            goals.append(goal)
        if goals:
            preferences["goals"] = goals

        # Pain points
        print("Enter pain points (enter empty line when done):")
        pain_points = []
        while True:
            point = input("- ")
            if not point.strip():
                break
            pain_points.append(point)
        if pain_points:
            preferences["pain_points"] = pain_points

        # Additional description
        description = input("Any additional information about your needs? ")
        if description.strip():
            preferences["description"] = description

        # Create user
        success = self.profile_manager.create_user(email, name, preferences)

        if success:
            print(f"\nSuccessfully onboarded {name} ({email})!")
            return True
        else:
            print(f"\nFailed to onboard user. Please check logs for details.")
            return False

    def close(self):
        """Close database connections"""
        self.profile_manager.close()


# Command-line interface
if __name__ == "__main__":
    onboarder = UserOnboarding()

    try:
        onboarder.onboard_user_interactive()
    finally:
        onboarder.close()
