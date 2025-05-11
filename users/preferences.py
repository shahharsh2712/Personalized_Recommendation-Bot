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


class PreferenceManager:
    """User-friendly preference management interface"""

    def __init__(self):
        self.profile_manager = UserProfileManager()

    def update_preferences_interactive(self, email):
        """Interactive console-based preference update"""
        # Get current user
        user = self.profile_manager.get_user(email)
        if not user:
            print(f"User not found: {email}")
            return False

        print(f"\n===== Update Preferences for {user['name']} =====\n")

        # Get current preferences
        current_preferences = user.get("preferences", {})

        # Display current preferences
        print("Current preferences:")
        if not current_preferences:
            print("  No preferences set yet.")
        else:
            for key, value in current_preferences.items():
                if isinstance(value, list):
                    print(f"  {key}: {', '.join(value)}")
                else:
                    print(f"  {key}: {value}")

        print("\nEnter new preferences (leave blank to keep current value):")

        # Collect new preferences
        new_preferences = {}

        # Interests
        current_interests = current_preferences.get("interests", [])
        interests_input = input(f"Interests [{', '.join(current_interests)}]: ")
        if interests_input.strip():
            new_preferences["interests"] = [
                interest.strip() for interest in interests_input.split(",")
            ]
        else:
            new_preferences["interests"] = current_interests

        # Categories
        current_categories = current_preferences.get("preferred_categories", [])
        categories_input = input(
            f"Preferred categories [{', '.join(current_categories)}]: "
        )
        if categories_input.strip():
            new_preferences["preferred_categories"] = [
                category.strip() for category in categories_input.split(",")
            ]
        else:
            new_preferences["preferred_categories"] = current_categories

        # Profession
        current_profession = current_preferences.get("profession", "")
        profession = input(f"Profession [{current_profession}]: ")
        if profession.strip():
            new_preferences["profession"] = profession
        else:
            new_preferences["profession"] = current_profession

        # Favorite tools
        current_tools = current_preferences.get("favorite_tools", [])
        tools_input = input(f"Favorite tools [{', '.join(current_tools)}]: ")
        if tools_input.strip():
            new_preferences["favorite_tools"] = [
                tool.strip() for tool in tools_input.split(",")
            ]
        else:
            new_preferences["favorite_tools"] = current_tools

        # Goals
        current_goals = current_preferences.get("goals", [])
        print("Goals (enter empty line when done):")
        for goal in current_goals:
            print(f"  - {goal}")

        goals = []
        while True:
            goal = input("- ")
            if not goal.strip():
                break
            goals.append(goal)
        if goals:
            new_preferences["goals"] = goals
        else:
            new_preferences["goals"] = current_goals

        # Pain points
        current_points = current_preferences.get("pain_points", [])
        print("Pain points (enter empty line when done):")
        for point in current_points:
            print(f"  - {point}")

        pain_points = []
        while True:
            point = input("- ")
            if not point.strip():
                break
            pain_points.append(point)
        if pain_points:
            new_preferences["pain_points"] = pain_points
        else:
            new_preferences["pain_points"] = current_points

        # Additional description
        current_desc = current_preferences.get("description", "")
        description = input(f"Additional information [{current_desc}]: ")
        if description.strip():
            new_preferences["description"] = description
        else:
            new_preferences["description"] = current_desc

        # Update preferences
        success = self.profile_manager.update_preferences(email, new_preferences)

        if success:
            print(f"\nSuccessfully updated preferences for {user['name']}!")
            return True
        else:
            print(f"\nFailed to update preferences. Please check logs for details.")
            return False

    def toggle_active_status(self, email):
        """Toggle a user's active status"""
        user = self.profile_manager.get_user(email)
        if not user:
            print(f"User not found: {email}")
            return False

        current_status = user.get("active", True)

        if current_status:
            success = self.profile_manager.deactivate_user(email)
            status_msg = "deactivated"
        else:
            success = self.profile_manager.reactivate_user(email)
            status_msg = "reactivated"

        if success:
            print(f"\nSuccessfully {status_msg} {user['name']} ({email})")
            return True
        else:
            print(f"\nFailed to update status. Please check logs for details.")
            return False

    def close(self):
        """Close database connections"""
        self.profile_manager.close()


# Command-line interface
if __name__ == "__main__":
    manager = PreferenceManager()

    try:
        print("\n===== User Preference Management =====")
        print("1. Update user preferences")
        print("2. Toggle active status")
        choice = input("\nEnter choice (1-2): ")

        email = input("Enter user email: ")

        if choice == "1":
            manager.update_preferences_interactive(email)
        elif choice == "2":
            manager.toggle_active_status(email)
        else:
            print("Invalid choice")
    finally:
        manager.close()
