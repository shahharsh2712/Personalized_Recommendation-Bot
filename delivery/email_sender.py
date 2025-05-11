import os
import logging
import sys
from datetime import datetime
from dotenv import load_dotenv
import jinja2
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Personalization, HtmlContent

# Import from our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storage.models import UserProfileStore, RecommendationStore

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EmailSender:
    """Sends personalized recommendation emails to users using SendGrid"""

    def __init__(self):
        # SendGrid configuration
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_name = os.getenv("SENDER_NAME", "App Recommendations")

        # Template engine
        self.template_loader = jinja2.FileSystemLoader(
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates"
            )
        )
        self.template_env = jinja2.Environment(loader=self.template_loader)

        # Database connections
        self.user_store = UserProfileStore()
        self.rec_store = RecommendationStore()

    def send_recommendations_email(self, user_email, recommendations=None, date=None):
        """Send a recommendations email to a specific user"""
        # Get user
        user = self.user_store.get_user_by_email(user_email)
        if not user:
            logger.error(f"User not found: {user_email}")
            return False

        user_id = str(user["_id"])

        # Get recommendations if not provided
        if not recommendations:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            recommendations = self.rec_store.get_user_recommendations(user_id, date)

        if not recommendations:
            logger.error(f"No recommendations found for user: {user_email}")
            return False

        # Prepare and send email
        success = self._send_recommendation_email(user, recommendations)

        # Log email delivery
        if success:
            self.rec_store.log_email_delivery(
                user_id,
                user_email,
                f"Your App Recommendations for {datetime.now().strftime('%b %d')}",
            )

        return success

    def _send_recommendation_email(self, user, recommendations):
        """Create and send a personalized recommendation email using SendGrid"""
        try:
            # Get the email template
            template = self.template_env.get_template("recommendation_email.html")

            # Render the template with data
            html_content = template.render(
                user_name=user["name"],
                recommendations=recommendations[:5],  # Limit to top 5
                date=datetime.now().strftime("%B %d, %Y"),
                unsubscribe_link=f"https://yourapp.com/unsubscribe?email={user['email']}",
            )

            # Create SendGrid message
            from_email = Email(self.sender_email, self.sender_name)
            to_email = To(user["email"])
            subject = f"Your App Recommendations for {datetime.now().strftime('%b %d')}"
            content = HtmlContent(html_content)

            message = Mail(
                from_email=from_email,
                to_emails=to_email,
                subject=subject,
                html_content=content,
            )

            # Send email via SendGrid
            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(message)

            # Check if email was sent successfully
            if response.status_code in [200, 201, 202]:
                logger.info(
                    f"Email sent successfully to {user['email']} (status code: {response.status_code})"
                )
                return True
            else:
                logger.error(
                    f"Failed to send email: status code {response.status_code}"
                )
                return False

        except Exception as e:
            logger.error(f"Error sending email to {user['email']}: {e}")
            return False

    def send_daily_recommendation_emails(self):
        """Send recommendation emails to all active users"""
        # Get today's date
        today = datetime.now().strftime("%Y-%m-%d")

        # Get all active users
        active_users = self.user_store.get_active_users()
        logger.info(f"Found {len(active_users)} active users for email delivery")

        # Track email sending success
        success_count = 0

        # Send emails to each user
        for user in active_users:
            try:
                email = user["email"]
                user_id = str(user["_id"])

                # Get recommendations for this user
                recommendations = self.rec_store.get_user_recommendations(
                    user_id, today
                )

                if not recommendations:
                    logger.warning(f"No recommendations found for {email} on {today}")
                    continue

                # Send email
                if self.send_recommendations_email(email, recommendations, today):
                    success_count += 1

            except Exception as e:
                logger.error(
                    f"Error sending recommendation email to {user.get('email', 'unknown')}: {e}"
                )

        logger.info(
            f"Successfully sent recommendation emails to {success_count}/{len(active_users)} users"
        )
        return success_count

    def close(self):
        """Close all database connections"""
        self.user_store.close()
        self.rec_store.close()


# Example usage
if __name__ == "__main__":
    # Create email template directory if it doesn't exist
    email_template_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates"
    )
    os.makedirs(email_template_dir, exist_ok=True)

    # Create a basic email template if it doesn't exist
    template_path = os.path.join(email_template_dir, "recommendation_email.html")
    if not os.path.exists(template_path):
        with open(template_path, "w") as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Your App Recommendations</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 20px; }
        .recommendation { margin-bottom: 25px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .app-name { font-size: 18px; font-weight: bold; color: #2a5885; }
        .tagline { font-style: italic; color: #555; }
        .reason { background-color: #f8f9fa; padding: 10px; border-radius: 4px; margin-top: 10px; }
        .footer { margin-top: 30px; font-size: 12px; color: #777; text-align: center; }
        .button { display: inline-block; background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Your App Recommendations</h1>
            <p>Hello {{ user_name }},</p>
            <p>Here are your personalized app recommendations for {{ date }}:</p>
        </div>
        
        {% for rec in recommendations %}
        <div class="recommendation">
            <div class="app-name">{{ rec.name }}</div>
            <div class="tagline">{{ rec.tagline }}</div>
            {% if rec.thumbnail %}
            <div style="text-align: center; margin: 15px 0;">
                <img src="{{ rec.thumbnail }}" alt="{{ rec.name }}" style="max-width: 200px; max-height: 150px;">
            </div>
            {% endif %}
            <div class="reason">
                <strong>Why we recommend it:</strong> {{ rec.reason }}
            </div>
            <div style="margin-top: 15px; text-align: center;">
                <a href="{{ rec.website }}" class="button">Check it out</a>
            </div>
        </div>
        {% endfor %}
        
        <div class="footer">
            <p>You're receiving this email because you subscribed to app recommendations.</p>
            <p><a href="{{ unsubscribe_link }}">Unsubscribe</a></p>
        </div>
    </div>
</body>
</html>""")

    # Check for SendGrid API key
    if not os.getenv("SENDGRID_API_KEY"):
        logger.error(
            "SendGrid API key not found in environment variables. Please add SENDGRID_API_KEY to your .env file."
        )
        sys.exit(1)

    email_sender = EmailSender()

    # Test with a specific user
    test_email = input("Enter email address to test: ")
    email_sender.send_recommendations_email(test_email)

    email_sender.close()
