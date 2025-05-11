import os
import sys
import argparse
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging directory
os.makedirs("personalized_recommendations/logs", exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("personalized_recommendations/logs/main.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def setup_parser():
    """Set up command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Personalized App Recommendation System"
    )

    parser.add_argument(
        "--mode",
        choices=["collect", "recommend", "email", "workflow", "scheduler", "onboard"],
        required=True,
        help="Operation mode",
    )

    parser.add_argument("--email", help="User email (for user-specific operations)")

    parser.add_argument(
        "--limit", type=int, default=20, help="Limit for number of products to collect"
    )

    return parser


def onboard_user(email=None):
    """Interactive user onboarding"""
    from users.profile import UserProfileManager

    profile_manager = UserProfileManager()

    # Get email if not provided
    if not email:
        email = input("Enter user email: ")

    # Check if user already exists
    existing_user = profile_manager.get_user(email)
    if existing_user:
        print(f"User {email} already exists!")
        update = (
            input("Would you like to update their preferences? (y/n): ").lower() == "y"
        )
        if not update:
            profile_manager.close()
            return

    # Get user information
    name = input("Enter user name: ")

    # Get preferences
    preferences = {}

    # Interests (comma-separated list)
    interests = input("Enter interests (comma-separated): ")
    if interests:
        preferences["interests"] = [i.strip() for i in interests.split(",")]

    # Categories (comma-separated list)
    categories = input("Enter preferred app categories (comma-separated): ")
    if categories:
        preferences["preferred_categories"] = [c.strip() for c in categories.split(",")]

    # Profession
    profession = input("Enter profession: ")
    if profession:
        preferences["profession"] = profession

    # Favorite tools (comma-separated list)
    tools = input("Enter favorite tools (comma-separated): ")
    if tools:
        preferences["favorite_tools"] = [t.strip() for t in tools.split(",")]

    # Description
    description = input("Enter additional description: ")
    if description:
        preferences["description"] = description

    # Create or update user
    if existing_user:
        success = profile_manager.update_preferences(email, preferences)
        message = "updated" if success else "failed to update"
    else:
        success = profile_manager.create_user(email, name, preferences)
        message = "created" if success else "failed to create"

    print(f"User {email} {message}!")
    profile_manager.close()


def main():
    """Main entry point"""
    parser = setup_parser()
    args = parser.parse_args()

    try:
        if args.mode == "collect":
            # Collect products
            from data.collector import ProductCollector

            collector = ProductCollector()
            products = collector.process_daily_pipeline()
            print(f"Collected {len(products)} products")

        elif args.mode == "recommend":
            # Generate recommendations
            from recommender.engine import RecommendationEngine

            engine = RecommendationEngine()

            if args.email:
                # Generate for specific user
                user = engine.user_manager.get_user(args.email)
                if user:
                    recs = engine.generate_recommendations_for_user(args.email)
                    print(f"Generated {len(recs)} recommendations for {args.email}")
                else:
                    print(f"User {args.email} not found")
            else:
                # Generate for all users
                count = engine.generate_daily_recommendations()
                print(f"Generated recommendations for {count} users")

            engine.close()

        elif args.mode == "email":
            # Send emails
            from delivery.email_sender import EmailSender

            sender = EmailSender()

            if args.email:
                # Send to specific user
                success = sender.send_recommendations_email(args.email)
                if success:
                    print(f"Email sent to {args.email}")
                else:
                    print(f"Failed to send email to {args.email}")
            else:
                # Send to all users
                count = sender.send_daily_recommendation_emails()
                print(f"Sent emails to {count} users")

            sender.close()

        elif args.mode == "workflow":
            # Run complete workflow
            from delivery.scheduler import daily_workflow

            daily_workflow()

        elif args.mode == "scheduler":
            # Run scheduler
            from delivery.scheduler import run_scheduler

            run_scheduler()

        elif args.mode == "onboard":
            # Onboard a user
            onboard_user(args.email)

    except Exception as e:
        logger.error(f"Error in main: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
