from datetime import datetime


class UserProfile:
    """Model representing a user profile for personalized recommendations."""

    def __init__(self, user_id, email):
        self.user_id = user_id
        self.email = email
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

        # Personal information
        self.name = ""
        self.job_role = ""
        self.industry = ""
        self.company_size = ""  # e.g., "1-10", "11-50", "51-200", "201-1000", "1000+"

        # Preferences
        self.interests = []  # List of interest areas e.g., ["marketing", "productivity"]
        self.tools_used = []  # List of tools already using
        self.challenges = []  # List of challenges they're facing
        self.budget_preference = ""  # e.g., "free", "freemium", "paid", "enterprise"

        # Enhanced data collection fields
        self.common_tasks = []  # Tasks the user spends most time on
        self.improvement_areas = []  # Areas the user wants to improve
        self.workflow_description = ""  # Free text description of workflow
        self.ideal_solution = ""  # Free text about ideal solution
        self.assessment_completeness = 0  # Percentage of profile completion

        # Engagement data
        self.last_login = datetime.now()
        self.recommendation_history = []  # Track what's been recommended
        self.product_interactions = {}  # Product ID -> interaction data

    def to_dict(self):
        """Convert profile to dictionary for storage."""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "name": self.name,
            "job_role": self.job_role,
            "industry": self.industry,
            "company_size": self.company_size,
            "interests": self.interests,
            "tools_used": self.tools_used,
            "challenges": self.challenges,
            "budget_preference": self.budget_preference,
            "last_login": self.last_login.isoformat(),
            "recommendation_history": self.recommendation_history,
            "product_interactions": self.product_interactions,
            # Add new fields to dictionary
            "common_tasks": self.common_tasks,
            "improvement_areas": self.improvement_areas,
            "workflow_description": self.workflow_description,
            "ideal_solution": self.ideal_solution,
            "assessment_completeness": self.assessment_completeness,
        }

    @classmethod
    def from_dict(cls, data):
        """Create profile from dictionary data."""
        profile = cls(data["user_id"], data["email"])

        profile.created_at = datetime.fromisoformat(
            data.get("created_at", datetime.now().isoformat())
        )
        profile.updated_at = datetime.fromisoformat(
            data.get("updated_at", datetime.now().isoformat())
        )
        profile.name = data.get("name", "")
        profile.job_role = data.get("job_role", "")
        profile.industry = data.get("industry", "")
        profile.company_size = data.get("company_size", "")
        profile.interests = data.get("interests", [])
        profile.tools_used = data.get("tools_used", [])
        profile.challenges = data.get("challenges", [])
        profile.budget_preference = data.get("budget_preference", "")
        profile.last_login = datetime.fromisoformat(
            data.get("last_login", datetime.now().isoformat())
        )
        profile.recommendation_history = data.get("recommendation_history", [])
        profile.product_interactions = data.get("product_interactions", {})

        # Load new fields from dictionary
        profile.common_tasks = data.get("common_tasks", [])
        profile.improvement_areas = data.get("improvement_areas", [])
        profile.workflow_description = data.get("workflow_description", "")
        profile.ideal_solution = data.get("ideal_solution", "")
        profile.assessment_completeness = data.get("assessment_completeness", 0)

        return profile
