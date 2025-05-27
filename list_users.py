import os
import sys
from datetime import datetime

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from personalized_recommendations.storage.models import UserProfileStore


def list_all_users():
    """List all users in the database"""
    store = UserProfileStore()

    try:
        # Get all users (not just active ones)
        users = list(store.db.db.user_profiles.find({}))

        if not users:
            print("No users found in the database.")
            return

        print(f"\nFound {len(users)} users:\n")
        print("-" * 80)

        for user in users:
            print(f"Email: {user.get('email', 'N/A')}")
            print(f"Name: {user.get('name', 'N/A')}")
            print(f"Active: {user.get('active', True)}")

            # Format last updated time
            last_updated = user.get("last_updated")
            if last_updated:
                if isinstance(last_updated, datetime):
                    last_updated = last_updated.strftime("%Y-%m-%d %H:%M:%S")
                print(f"Last Updated: {last_updated}")

            # Show preferences
            preferences = user.get("preferences", {})
            if preferences:
                print("\nPreferences:")
                for key, value in preferences.items():
                    if isinstance(value, list):
                        print(f"  {key}: {', '.join(value)}")
                    else:
                        print(f"  {key}: {value}")

            print("-" * 80)

    except Exception as e:
        print(f"Error listing users: {e}")
    finally:
        store.close()


if __name__ == "__main__":
    list_all_users()
