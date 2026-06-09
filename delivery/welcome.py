"""Send a one-time welcome email with personalized recommendations after profile setup."""
import logging

logger = logging.getLogger(__name__)


def send_welcome_email(user_email):
    """
    Generate recommendations for user_email and send a welcome email.
    Returns True if the email was sent. Skips if already sent or on failure.
    """
    from recommender.engine import RecommendationEngine
    from delivery.email_sender import EmailSender
    from users.profile import UserProfileManager

    manager = UserProfileManager()
    try:
        user = manager.get_user(user_email)
        if not user:
            logger.warning("Welcome email skipped — user not in MongoDB: %s", user_email)
            return False
        if user.get("welcome_email_sent"):
            logger.info("Welcome email already sent for %s", user_email)
            return False

        engine = RecommendationEngine()
        try:
            recommendations = engine.generate_recommendations_for_user(user_email)
        finally:
            engine.close()

        if not recommendations:
            logger.warning("Welcome email skipped — no recommendations for %s", user_email)
            return False

        sender = EmailSender()
        try:
            sent = sender.send_welcome_email(user_email, recommendations)
        finally:
            sender.close()

        if sent:
            user["welcome_email_sent"] = True
            manager.store.save_user(user)
            logger.info("Welcome email sent to %s", user_email)
        return sent
    except Exception as e:
        logger.error("Welcome email failed for %s: %s", user_email, e)
        return False
    finally:
        manager.close()
