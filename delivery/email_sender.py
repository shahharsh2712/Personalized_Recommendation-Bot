import os
import logging
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
import jinja2

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
    """Sends personalized recommendation emails via SMTP (Gmail) or SendGrid."""

    def __init__(self):
        self.provider = (os.getenv("EMAIL_PROVIDER") or "smtp").lower()
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_name = os.getenv("SENDER_NAME", "App Recommendations")
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER") or self.sender_email
        self.smtp_password = os.getenv("SMTP_PASSWORD")

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

    def _render_email_html(self, user, recommendations):
        template = self.template_env.get_template("recommendation_email.html")
        return template.render(
            user_name=user["name"],
            recommendations=recommendations[:5],
            date=datetime.now().strftime("%B %d, %Y"),
            unsubscribe_link=f"https://yourapp.com/unsubscribe?email={user['email']}",
        )

    def _send_via_smtp(self, to_email, subject, html_content):
        if not self.smtp_password:
            raise ValueError("SMTP_PASSWORD is not set in .env")
        if not self.sender_email:
            raise ValueError("SENDER_EMAIL is not set in .env")

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{self.sender_name} <{self.sender_email}>"
        message["To"] = to_email
        message.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.sender_email, [to_email], message.as_string())

        logger.info(f"Email sent via SMTP to {to_email}")
        return True

    def _send_via_sendgrid(self, to_email, subject, html_content):
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, HtmlContent

        message = Mail(
            from_email=Email(self.sender_email, self.sender_name),
            to_emails=To(to_email),
            subject=subject,
            html_content=HtmlContent(html_content),
        )
        response = SendGridAPIClient(self.sendgrid_api_key).send(message)
        if response.status_code in [200, 201, 202]:
            logger.info(
                f"Email sent via SendGrid to {to_email} (status {response.status_code})"
            )
            return True
        logger.error(f"SendGrid failed: status {response.status_code}")
        return False

    def _send_recommendation_email(self, user, recommendations):
        try:
            html_content = self._render_email_html(user, recommendations)
            subject = f"Your App Recommendations for {datetime.now().strftime('%b %d')}"
            to_email = user["email"]

            if self.provider == "sendgrid":
                return self._send_via_sendgrid(to_email, subject, html_content)
            return self._send_via_smtp(to_email, subject, html_content)

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

    provider = (os.getenv("EMAIL_PROVIDER") or "smtp").lower()
    if provider == "sendgrid" and not os.getenv("SENDGRID_API_KEY"):
        logger.error("EMAIL_PROVIDER=sendgrid requires SENDGRID_API_KEY in .env")
        sys.exit(1)
    if provider == "smtp" and not os.getenv("SMTP_PASSWORD"):
        logger.error("EMAIL_PROVIDER=smtp requires SMTP_PASSWORD (Gmail app password) in .env")
        sys.exit(1)

    email_sender = EmailSender()

    # Test with a specific user
    test_email = input("Enter email address to test: ")
    email_sender.send_recommendations_email(test_email)

    email_sender.close()
