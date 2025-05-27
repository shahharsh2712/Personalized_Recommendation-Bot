import os
import logging
import time
import schedule
from datetime import datetime
from dotenv import load_dotenv

# Import from our modules
from personalized_recommendations.data.collector import ProductCollector
from personalized_recommendations.recommender.engine import RecommendationEngine
from personalized_recommendations.delivery.email_sender import EmailSender
from personalized_recommendations.storage.models import ProductStore
from personalized_recommendations.src.perplexity_enrich_products import enrich_products
from personalized_recommendations.src.generate_embeddings import generate_embeddings

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("personalized_recommendations/logs/scheduler.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def validate_mongodb_connection():
    """Validate MongoDB connection and collections"""
    try:
        store = ProductStore()
        # Test connection by listing collections
        collections = store.db.list_collection_names()
        logger.info(f"Connected to MongoDB. Available collections: {collections}")
        store.close()
        return True
    except Exception as e:
        logger.error(f"MongoDB connection validation failed: {e}")
        return False


def collect_and_enrich_products():
    """Collect and enrich products using Perplexity API"""
    logger.info("Starting product collection and enrichment job")
    start_time = datetime.now()

    try:
        collector = ProductCollector()
        products = collector.process_daily_pipeline()

        if not products:
            logger.warning("No products collected")
            return 0

        # No need for additional enrichment of all products
        # products are already enriched in the pipeline
        success_count = len(products)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(
            f"Product collection and enrichment completed in {duration:.2f} seconds"
        )
        logger.info(
            f"Collected, enriched, and saved {success_count} products to MongoDB"
        )

        return success_count
    except Exception as e:
        logger.error(f"Error in product collection and enrichment job: {e}")
        return 0


def generate_and_save_embeddings():
    """Generate embeddings for products and save to MongoDB"""
    logger.info("Starting embeddings generation job")
    start_time = datetime.now()

    try:
        products_with_embeddings = generate_embeddings()

        if not products_with_embeddings:
            logger.warning("No embeddings generated")
            return 0

        # Save products with embeddings to MongoDB
        store = ProductStore()
        success_count = store.save_batch(products_with_embeddings)
        store.close()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Embeddings generation completed in {duration:.2f} seconds")
        logger.info(
            f"Generated and saved embeddings for {success_count} products to MongoDB"
        )

        return success_count
    except Exception as e:
        logger.error(f"Error in embeddings generation job: {e}")
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

    # Step 0: Validate MongoDB connection
    if not validate_mongodb_connection():
        logger.error("MongoDB connection validation failed. Aborting workflow.")
        return

    # Step 1: Collect and enrich products
    product_count = collect_and_enrich_products()
    if product_count == 0:
        logger.warning("No products collected and enriched. Aborting workflow.")
        return

    # Step 2: Generate recommendations
    user_count = generate_recommendations_job()
    if user_count == 0:
        logger.warning("No recommendations generated. Aborting workflow.")
        return

    # Step 3: Send emails
    email_count = send_emails_job()

    logger.info(
        f"Daily workflow complete: {product_count} products collected and enriched, "
        f"recommendations for {user_count} users, "
        f"emails sent to {email_count} users"
    )


def run_scheduler():
    """Run the scheduler"""
    logger.info("Starting recommendation system scheduler")

    # Schedule daily workflow at specific times
    schedule.every().day.at("05:00").do(daily_workflow)

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
