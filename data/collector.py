import os
import sys
import json
import logging
import time
from datetime import datetime

# Add the src directory to path so we can import existing modules
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)

# Import from existing codebase
from fetch_products import fetch_products, process_products
from perplexity_enrich_products import enrich_with_perplexity, create_embedding_text
from generate_embeddings import generate_embedding
from categorize_all_products import categorize_product

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ProductCollector:
    """Collects product data from Product Hunt, reusing existing functionality"""

    def __init__(self):
        # Create necessary directories
        os.makedirs("personalized_recommendations/data_store", exist_ok=True)
        os.makedirs("personalized_recommendations/logs", exist_ok=True)

    def collect_daily_products(self, max_products=20):
        """Collect today's new products from Product Hunt"""
        logger.info("Starting daily product collection...")

        date_string = datetime.now().strftime("%Y-%m-%d")

        # Collect products (limit to max_products)
        cursor = None
        has_next_page = True
        all_products = []
        batch_size = min(max_products, 20)  # API supports up to 20 at once

        while has_next_page and len(all_products) < max_products:
            logger.info(
                f"Fetching batch of products (current count: {len(all_products)})"
            )

            # Fetch a batch of products using existing function
            products_data = fetch_products(cursor, batch_size)

            if not products_data:
                logger.error("Error fetching products. Stopping.")
                break

            # Process products using existing function
            processed_batch = process_products(products_data)
            all_products.extend(processed_batch)

            # Update pagination info
            if "pageInfo" in products_data:
                cursor = products_data["pageInfo"].get("endCursor")
                has_next_page = products_data["pageInfo"].get("hasNextPage", False)
            else:
                has_next_page = False

            # Respect API rate limits
            time.sleep(1)

        # Trim to max size if needed
        if len(all_products) > max_products:
            all_products = all_products[:max_products]

        logger.info(f"Collected {len(all_products)} products for {date_string}")

        # Save raw products for this date
        output_file = (
            f"personalized_recommendations/data_store/raw_products_{date_string}.json"
        )
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_products, f, indent=2, ensure_ascii=False)

        return all_products

    def enrich_products(self, products):
        """Enrich products with detailed information"""
        if not products:
            logger.info("No products to enrich")
            return []

        enriched_products = []
        for i, product in enumerate(products):
            logger.info(f"Enriching product {i + 1}/{len(products)}: {product['name']}")

            try:
                # Enrich with Perplexity using existing function
                enriched_product = enrich_with_perplexity(product)

                # Add embedding-optimized text using existing function
                enriched_product["embedding_text"] = create_embedding_text(
                    enriched_product
                )

                # Add source information
                enriched_product["data_sources"] = {
                    "product_hunt": True,
                    "perplexity_enhanced": True,
                    "collection_date": datetime.now().strftime("%Y-%m-%d"),
                }

                enriched_products.append(enriched_product)

                # Respect API rate limits
                logger.info("Waiting for rate limits...")
                time.sleep(3)

            except Exception as e:
                logger.error(f"Error enriching product {product['name']}: {e}")

        # Save enriched products
        date_string = datetime.now().strftime("%Y-%m-%d")
        output_file = f"personalized_recommendations/data_store/enriched_products_{date_string}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(enriched_products, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(enriched_products)} enriched products")
        return enriched_products

    def generate_embeddings(self, products):
        """Generate embeddings for products"""
        if not products:
            logger.info("No products to embed")
            return []

        products_with_embeddings = []
        for i, product in enumerate(products):
            logger.info(
                f"Generating embedding for product {i + 1}/{len(products)}: {product['name']}"
            )

            try:
                # Generate embedding using existing function
                if "embedding_text" in product:
                    embedding = generate_embedding(product["embedding_text"])
                    if embedding:
                        product["embedding"] = embedding
                        products_with_embeddings.append(product)
                    else:
                        logger.error(
                            f"Failed to generate embedding for {product['name']}"
                        )
                else:
                    logger.error(f"No embedding_text found for {product['name']}")

                # Respect API rate limits
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Error generating embedding for {product['name']}: {e}")

        # Save products with embeddings
        date_string = datetime.now().strftime("%Y-%m-%d")
        output_file = f"personalized_recommendations/data_store/products_with_embeddings_{date_string}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(products_with_embeddings, f, indent=2, ensure_ascii=False)

        # Save to MongoDB
        from storage.models import ProductStore

        store = ProductStore()
        store.save_batch(products_with_embeddings)
        store.close()

        logger.info(
            f"Saved {len(products_with_embeddings)} products with embeddings and stored in MongoDB"
        )
        return products_with_embeddings

    def process_daily_pipeline(self):
        """Run the full daily collection pipeline"""
        logger.info("Starting daily product pipeline")

        # Step 1: Collect raw products
        raw_products = self.collect_daily_products(max_products=20)

        # Step 2: Enrich products
        enriched_products = self.enrich_products(raw_products)

        # Step 3: Generate embeddings
        products_with_embeddings = self.generate_embeddings(enriched_products)

        logger.info(
            f"Pipeline complete: {len(raw_products)} collected, "
            f"{len(enriched_products)} enriched, "
            f"{len(products_with_embeddings)} with embeddings"
        )

        return products_with_embeddings


# Example usage
if __name__ == "__main__":
    collector = ProductCollector()
    collector.process_daily_pipeline()
