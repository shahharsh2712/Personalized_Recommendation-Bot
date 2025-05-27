import json
import os
import time
import requests
import re
from dotenv import load_dotenv
import logging
from datetime import datetime
from personalized_recommendations.storage.models import ProductStore

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("personalized_recommendations/logs/enrichment.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")


def enrich_with_perplexity(product):
    """Use Perplexity Sonar API to get and structure product information"""
    url = "https://api.perplexity.ai/chat/completions"

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }

    # Create a query that asks for specific structured information
    query = f"""
I need comprehensive information about {product["name"]} ({product["website"]}), a product with the tagline: "{product["tagline"]}".

Please provide the information in the following JSON format:
{{
  "detailed_description": "5-8 sentences explaining what this product does, its main purpose, and what problems it solves",
  
  "features": [
    "Detailed feature 1 with explanation of its benefit",
    "Detailed feature 2 with explanation of its benefit",
    "Detailed feature 3 with explanation of its benefit",
    "Detailed feature 4 with explanation of its benefit",
    "Detailed feature 5 with explanation of its benefit"
  ],
  
  "pricing": {{
    "model": "Free/Freemium/Subscription/One-time purchase/etc.",
    "tiers": [
      "Free tier: what's included in free version",
      "Tier 1: name, price, and what's included",
      "Tier 2: name, price, and what's included",
      "Enterprise: details if available"
    ],
    "free_trial": "Details about any free trial",
    "additional_info": "Any other relevant pricing information"
  }},
  
  "use_cases": [
    "Detailed use case 1 - specific scenario where this product is useful",
    "Detailed use case 2 - specific scenario where this product is useful",
    "Detailed use case 3 - specific scenario where this product is useful"
  ],
  
  "target_audience": "Who this product is designed for (company size, roles, industries)"
}}

Focus on finding accurate, detailed information, especially about the product's functionality and pricing. The JSON should be properly formatted without any additional text.
"""

    data = {
        "model": "sonar",  # Using the model from the cookbook example
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that provides detailed information about software products. Always format your response as valid JSON according to the user's specified structure.",
            },
            {"role": "user", "content": query},
        ],
        "temperature": 0.2,
        "max_tokens": 2000,  # Ensure we get a complete response
    }

    try:
        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Extract JSON from the response
            json_match = re.search(r"({.*})", content, re.DOTALL)
            if json_match:
                content = json_match.group(1)

            try:
                enriched_data = json.loads(content)
                # Update the product with enriched data
                product.update(enriched_data)
                return product
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON for {product['name']}: {e}")
                print(f"Raw content: {content}")

                # Try to clean up the JSON and parse again
                try:
                    # Replace common issues in malformed JSON
                    cleaned_content = content.replace("'", '"')
                    # Try to fix trailing commas
                    cleaned_content = re.sub(r",\s*}", "}", cleaned_content)
                    cleaned_content = re.sub(r",\s*]", "]", cleaned_content)

                    enriched_data = json.loads(cleaned_content)
                    product.update(enriched_data)
                    return product
                except:
                    print("Failed to clean and parse JSON")
                    return product
        else:
            print(f"Error from Perplexity API: {response.status_code}")
            print(f"Response: {response.text}")

            # If we hit rate limits, wait and retry
            if response.status_code == 429:
                print("Rate limit hit, waiting 60 seconds...")
                time.sleep(60)
                return enrich_with_perplexity(product)  # Retry

            return product
    except Exception as e:
        print(f"Exception when calling Perplexity API: {e}")
        return product


def create_embedding_text(product):
    """Create optimized text representation for embedding generation"""

    # Start with product name and category
    embedding_text = f"Product: {product['name']}\n\n"

    # Add detailed description
    if "detailed_description" in product:
        embedding_text += f"Description: {product['detailed_description']}\n\n"

    # Add features with emphasis
    if "features" in product and product["features"]:
        embedding_text += "Key Features:\n"
        for feature in product["features"]:
            embedding_text += f"- {feature}\n"
        embedding_text += "\n"

    # Add pricing information in a structured way
    if "pricing" in product:
        pricing = product["pricing"]
        embedding_text += f"Pricing Model: {pricing.get('model', 'N/A')}\n"

        if "tiers" in pricing and pricing["tiers"]:
            embedding_text += "Pricing Tiers:\n"
            for tier in pricing["tiers"]:
                embedding_text += f"- {tier}\n"

        if "free_trial" in pricing and pricing["free_trial"]:
            embedding_text += f"Free Trial: {pricing['free_trial']}\n"

        embedding_text += "\n"

    # Add use cases with emphasis
    if "use_cases" in product and product["use_cases"]:
        embedding_text += "Use Cases:\n"
        for use_case in product["use_cases"]:
            embedding_text += f"- {use_case}\n"
        embedding_text += "\n"

    # Add target audience
    if "target_audience" in product:
        embedding_text += f"Target Audience: {product['target_audience']}\n\n"

    # Add original topics/categories for additional context
    if "topics" in product and product["topics"]:
        embedding_text += f"Categories: {', '.join(product['topics'])}\n"

    return embedding_text


def save_checkpoint(products, filename):
    """Save a checkpoint of the current progress"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"Saved checkpoint to {filename}")


def enrich_products():
    """Enrich products using Perplexity API and save to MongoDB"""
    logger.info("Starting product enrichment")
    start_time = datetime.now()

    try:
        # Load products from MongoDB
        store = ProductStore()
        products = store.get_all_products()

        if not products:
            logger.warning("No products found in MongoDB")
            return []

        enriched_products = []
        for product in products:
            try:
                # Add enrichment logic here
                # For now, we'll just add a timestamp
                product["enriched_at"] = datetime.now().isoformat()
                enriched_products.append(product)

                # Add a small delay to avoid rate limiting
                time.sleep(0.1)

            except Exception as e:
                logger.error(
                    f"Error enriching product {product.get('id', 'unknown')}: {e}"
                )
                continue

        if not enriched_products:
            logger.warning("No products were successfully enriched")
            return []

        # Save enriched products to MongoDB
        success_count = store.save_batch(enriched_products)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Product enrichment completed in {duration:.2f} seconds")
        logger.info(
            f"Successfully enriched and saved {success_count} products to MongoDB"
        )

        return enriched_products

    except Exception as e:
        logger.error(f"Error in product enrichment: {e}")
        return []
    finally:
        store.close()


if __name__ == "__main__":
    enrich_products()
