import json
import os
from datetime import datetime
from models.user_profile import UserProfile


class UserRepository:
    """Repository for managing user profiles."""

    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.profiles_file = os.path.join(data_dir, "user_profiles.json")
        self.users_file = os.path.join(
            data_dir, "users.json"
        )  # For storing credentials
        self.profiles = {}
        self.users = {}  # {email -> {password_hash, user_id}}
        self._load_data()

    def _load_data(self):
        """Load profiles and users data from storage."""
        # Load profiles
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, "r", encoding="utf-8") as f:
                    profiles_data = json.load(f)
                    for user_id, profile_data in profiles_data.items():
                        self.profiles[user_id] = UserProfile.from_dict(profile_data)
                print(f"Loaded {len(self.profiles)} user profiles")
            except Exception as e:
                print(f"Error loading profiles: {e}")
                self.profiles = {}

        # Load users
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, "r", encoding="utf-8") as f:
                    self.users = json.load(f)
                print(f"Loaded {len(self.users)} user accounts")
            except Exception as e:
                print(f"Error loading users: {e}")
                self.users = {}

    def _save_profiles(self):
        """Save profiles to storage."""
        os.makedirs(self.data_dir, exist_ok=True)

        profiles_data = {
            user_id: profile.to_dict() for user_id, profile in self.profiles.items()
        }

        with open(self.profiles_file, "w", encoding="utf-8") as f:
            json.dump(profiles_data, f, indent=2, ensure_ascii=False)

    def _save_users(self):
        """Save users to storage."""
        os.makedirs(self.data_dir, exist_ok=True)

        with open(self.users_file, "w", encoding="utf-8") as f:
            json.dump(self.users, f, indent=2, ensure_ascii=False)

    def get_profile(self, user_id):
        """Get a user profile by ID."""
        return self.profiles.get(user_id)

    def get_user_by_email(self, email):
        """Get a user by email."""
        return self.users.get(email)

    def create_user(self, email, password_hash, name=""):
        """Create a new user."""
        if email in self.users:
            raise ValueError(f"User already exists with email {email}")

        user_id = str(len(self.users) + 1)  # Simple ID generation

        # Create the user entry
        self.users[email] = {"password_hash": password_hash, "user_id": user_id}
        self._save_users()

        # Create the profile
        profile = UserProfile(user_id, email)
        profile.name = name
        self.profiles[user_id] = profile
        self._save_profiles()

        return user_id

    def update_profile(self, user_id, profile_data):
        """Update a user profile."""
        if user_id not in self.profiles:
            raise ValueError(f"No profile found for user {user_id}")

        profile = self.profiles[user_id]

        # Update fields from profile_data
        for key, value in profile_data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        profile.updated_at = datetime.now()
        self._save_profiles()
        return profile

    def delete_user(self, user_id):
        """Delete a user and their profile."""
        # Find and remove the user entry
        email_to_remove = None
        for email, user_data in self.users.items():
            if user_data["user_id"] == user_id:
                email_to_remove = email
                break

        if email_to_remove:
            del self.users[email_to_remove]
            self._save_users()

        # Remove the profile
        if user_id in self.profiles:
            del self.profiles[user_id]
            self._save_profiles()
            return True
        return False

    def get_all_profiles(self):
        """Get all user profiles."""
        return list(self.profiles.values())
