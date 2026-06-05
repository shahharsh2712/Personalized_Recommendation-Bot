"""Sync Flask frontend profiles to MongoDB (used by recommend + email pipeline)."""
import logging
import os
import sys

from app_paths import PROJECT_ROOT

logger = logging.getLogger(__name__)


def _ensure_project_path():
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)


def frontend_profile_to_preferences(profile):
    """Map web UI profile fields to MongoDB preferences format."""
    preferences = {}

    if profile.interests:
        preferences["interests"] = profile.interests
    if profile.job_role:
        preferences["profession"] = profile.job_role
    if profile.tools_used:
        preferences["favorite_tools"] = profile.tools_used
    if profile.challenges:
        preferences["pain_points"] = profile.challenges

    goals = []
    if profile.improvement_areas:
        goals.extend(
            area.replace("_", " ").title() for area in profile.improvement_areas
        )
    if profile.common_tasks:
        goals.extend(task.replace("_", " ").title() for task in profile.common_tasks)
    if goals:
        preferences["goals"] = goals

    description_parts = []
    if profile.industry:
        description_parts.append(f"Industry: {profile.industry}")
    if profile.company_size:
        description_parts.append(f"Company size: {profile.company_size}")
    if profile.workflow_description:
        description_parts.append(profile.workflow_description)
    if profile.ideal_solution:
        description_parts.append(profile.ideal_solution)
    if profile.budget_preference:
        description_parts.append(f"Budget preference: {profile.budget_preference}")
    if description_parts:
        preferences["description"] = "\n".join(description_parts)

    if profile.industry:
        preferences.setdefault("preferred_categories", []).append(profile.industry)

    return preferences


def sync_profile_to_mongodb(profile):
    """
    Create or update user_profiles in MongoDB from a frontend UserProfile.
    Returns True on success.
    """
    if not profile or not profile.email:
        return False

    _ensure_project_path()
    from users.profile import UserProfileManager

    preferences = frontend_profile_to_preferences(profile)
    name = profile.name or profile.email.split("@")[0]

    manager = UserProfileManager()
    try:
        existing = manager.get_user(profile.email)
        if existing:
            if preferences:
                manager.update_preferences(profile.email, preferences)
            existing = manager.get_user(profile.email) or existing
            existing["name"] = name
            existing["active"] = True
            manager.store.save_user(existing)
            logger.info("Updated MongoDB profile for %s", profile.email)
        else:
            manager.create_user(
                profile.email, name, preferences=preferences or None, active=True
            )
            logger.info("Created MongoDB profile for %s", profile.email)
        return True
    except Exception as e:
        logger.error("MongoDB sync failed for %s: %s", profile.email, e)
        return False
    finally:
        manager.close()
