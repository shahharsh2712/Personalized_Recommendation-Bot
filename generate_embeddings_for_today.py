import sys
import os

# Load .env from the current directory (personalized_recommendations)
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

import json
from personalized_recommendations.data.collector import ProductCollector

date_string = "2025-05-11"
enriched_file = f"data_store/enriched_products_{date_string}.json"

with open(enriched_file, "r", encoding="utf-8") as f:
    enriched_products = json.load(f)

# Patch ProductCollector to save embeddings in the correct data_store directory
from personalized_recommendations.data.collector import ProductCollector


class PatchedProductCollector(ProductCollector):
    def generate_embeddings(self, products):
        if not products:
            self.logger.info("No products to embed")
            return []
        products_with_embeddings = []
        for i, product in enumerate(products):
            self.logger.info(
                f"Generating embedding for product {i + 1}/{len(products)}: {product['name']}"
            )
            try:
                if "embedding_text" in product:
                    from generate_embeddings import generate_embedding

                    embedding = generate_embedding(product["embedding_text"])
                    if embedding:
                        product["embedding"] = embedding
                        products_with_embeddings.append(product)
                    else:
                        self.logger.error(
                            f"Failed to generate embedding for {product['name']}"
                        )
                else:
                    self.logger.error(f"No embedding_text found for {product['name']}")
                import time

                time.sleep(0.5)
            except Exception as e:
                self.logger.error(
                    f"Error generating embedding for {product['name']}: {e}"
                )
        # Save products with embeddings in the correct directory
        output_file = f"data_store/products_with_embeddings_{date_string}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(products_with_embeddings, f, indent=2, ensure_ascii=False)
        from personalized_recommendations.storage.models import ProductStore

        store = ProductStore()
        store.save_batch(products_with_embeddings)
        store.close()
        self.logger.info(
            f"Saved {len(products_with_embeddings)} products with embeddings and stored in MongoDB"
        )
        return products_with_embeddings


collector = PatchedProductCollector()
collector.generate_embeddings(enriched_products)
