import os
import json
import logging
import time
from datetime import datetime
from dotenv import load_dotenv
from personalized_recommendations.storage.models import ProductStore
from openai import OpenAI

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("personalized_recommendations/logs/embeddings.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_embedding(text):
    """Generate embedding for a text using OpenAI's API"""
    try:
        response = client.embeddings.create(model="text-embedding-3-small", input=text)
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None


def generate_embeddings(products):
    """Generate embeddings for a list of products and save to MongoDB"""
    logger.info("Starting embeddings generation")
    start_time = datetime.now()

    if not products:
        logger.warning("No products provided for embedding generation")
        return []

    store = ProductStore()
    products_with_embeddings = []
    for product in products:
        try:
            embedding_text = (
                product.get("embedding_text")
                or product.get("description")
                or product.get("name")
            )
            if not embedding_text:
                logger.warning(
                    f"No text found for embedding for product {product.get('name', 'unknown')}"
                )
                continue
            embedding = generate_embedding(embedding_text)
            if embedding:
                product["embedding"] = embedding
                product["embedding_generated_at"] = datetime.now().isoformat()
                products_with_embeddings.append(product)
            else:
                logger.warning(
                    f"Failed to generate embedding for {product.get('name', 'unknown')}"
                )
                continue
            # Respect API rate limits
            time.sleep(0.5)
        except Exception as e:
            logger.error(
                f"Error generating embedding for product {product.get('id', 'unknown')}: {e}"
            )
            continue

    if not products_with_embeddings:
        logger.warning("No embeddings were successfully generated")
        return []

    # Save products with embeddings to MongoDB
    success_count = store.save_batch(products_with_embeddings)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Embeddings generation completed in {duration:.2f} seconds")
    logger.info(
        f"Successfully generated and saved embeddings for {success_count} products to MongoDB"
    )

    store.close()
    return products_with_embeddings


if __name__ == "__main__":
    generate_embeddings()
