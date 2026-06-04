import os
import logging
import time
import schedule
from datetime import datetime
from dotenv import load_dotenv

# Import from our modules
from data.collector import ProductCollector
from recommender.engine import RecommendationEngine
from delivery.email_sender import EmailSender

# Load environment variables
load_dotenv()

os.makedirs("logs", exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/scheduler.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def collect_products_job():
    """Job to collect new products"""
    logger.info("Starting product collection job")
    start_time = datetime.now()

    try:
        collector = ProductCollector()
        products = collector.process_daily_pipeline()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Product collection completed in {duration:.2f} seconds")
        logger.info(f"Collected and processed {len(products)} products")

        return len(products)
    except Exception as e:
        logger.error(f"Error in product collection job: {e}")
        return 0


def generate_recommendations_job():
    """Job to generate recommendations for all users"""
    logger.info("Starting recommendation generation job")
    start_time = datetime.now()

    try:
        engine = RecommendationEngine()
        count = engine.generate_daily_recommendations()
        engine.close()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Recommendation generation completed in {duration:.2f} seconds")
        logger.info(f"Generated recommendations for {count} users")

        return count
    except Exception as e:
        logger.error(f"Error in recommendation generation job: {e}")
        return 0


def send_emails_job():
    """Job to send recommendation emails to users"""
    logger.info("Starting email delivery job")
    start_time = datetime.now()

    try:
        sender = EmailSender()
        count = sender.send_daily_recommendation_emails()
        sender.close()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Email delivery completed in {duration:.2f} seconds")
        logger.info(f"Sent emails to {count} users")

        return count
    except Exception as e:
        logger.error(f"Error in email delivery job: {e}")
        return 0


def daily_workflow():
    """Run the complete daily workflow"""
    logger.info("Starting daily workflow")

    # Step 1: Collect new products
    product_count = collect_products_job()

    # If no products were collected, we might want to stop
    if product_count == 0:
        logger.warning("No products collected, skipping recommendation and email steps")
        return

    # Step 2: Generate recommendations
    user_count = generate_recommendations_job()

    # Step 3: Send emails
    email_count = send_emails_job()

    logger.info(
        f"Daily workflow complete: {product_count} products collected, "
        f"recommendations for {user_count} users, "
        f"emails sent to {email_count} users"
    )


def run_scheduler():
    """Run the scheduler"""
    logger.info("Starting recommendation system scheduler")

    # Schedule daily workflow at specific times
    # Collection early morning
    schedule.every().day.at("05:00").do(collect_products_job)
    # Generate recommendations a bit later
    schedule.every().day.at("06:00").do(generate_recommendations_job)
    # Send emails in the morning when people check email
    schedule.every().day.at("08:00").do(send_emails_job)

    # Alternative: schedule the complete workflow
    # schedule.every().day.at("08:00").do(daily_workflow)

    logger.info("Scheduler running. Press Ctrl+C to exit.")

    # Run the loop
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    # Option 1: Run the scheduler
    run_scheduler()

    # Option 2: Run jobs manually
    # daily_workflow()
