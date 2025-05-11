import json
import os
import time
import requests
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
I need comprehensive information about {product["name"]} ({product.get("website", "N/A")}), a product with the tagline: "{product["tagline"]}".

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


def main():
    # Check if checkpoint exists and load it
    checkpoint_file = (
        "data/enriched_popular_products_checkpoint.json"  # New checkpoint file
    )
    start_index = 0
    enriched_products = []

    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                enriched_products = json.load(f)
            start_index = len(enriched_products)
            print(f"Loaded checkpoint with {start_index} already enriched products")
        except Exception as e:
            print(f"Error loading checkpoint: {e}")
            enriched_products = []

    # Load popular products
    with open(
        "data/categorized_products.json", "r", encoding="utf-8"
    ) as f:  # Changed input file
        all_products = json.load(f)

    total_products = len(all_products)
    print(f"Loaded {total_products} popular products")

    # We can process all products or limit for testing
    all_products_to_enrich = all_products  # Process all popular products

    # Skip products that have already been processed
    products_to_enrich = all_products_to_enrich[start_index:]

    print(f"Starting enrichment from product {start_index + 1}")
    print(f"Remaining products to enrich: {len(products_to_enrich)}")

    for i, product in enumerate(products_to_enrich):
        current_index = start_index + i
        print(
            f"Enriching product {current_index + 1}/{len(all_products_to_enrich)}: {product['name']}"
        )

        # Enrich with Perplexity
        enriched_product = enrich_with_perplexity(product)

        # Add embedding-optimized text
        enriched_product["embedding_text"] = create_embedding_text(enriched_product)

        # Add source information
        enriched_product["data_sources"] = {
            "product_hunt": True,
            "perplexity_enhanced": True,
        }

        enriched_products.append(enriched_product)

        # Save checkpoint every 5 products
        if (current_index + 1) % 5 == 0 or (current_index + 1) == len(
            all_products_to_enrich
        ):
            save_checkpoint(enriched_products, checkpoint_file)

        # Respect API rate limits - wait longer to avoid rate limits
        print(f"  Waiting for rate limits...")
        time.sleep(3)  # Increased wait time to 3 seconds

    # Save enriched products
    with open(
        "data/enriched_popular_products.json", "w", encoding="utf-8"
    ) as f:  # Changed output file
        json.dump(enriched_products, f, indent=2, ensure_ascii=False)

    print(
        f"Saved {len(enriched_products)} enriched products to data/enriched_popular_products.json"
    )

    # Print a sample
    if enriched_products:
        print("\nSample enriched product:")
        sample = enriched_products[0]
        print(f"Name: {sample['name']}")
        print(f"Description: {sample.get('detailed_description', 'N/A')}")
        print("Features:")
        for feature in sample.get("features", ["N/A"]):
            print(f"  - {feature}")
        print("Pricing:")
        if "pricing" in sample:
            print(f"  Model: {sample['pricing'].get('model', 'N/A')}")
            print(f"  Tiers:")
            for tier in sample["pricing"].get("tiers", ["N/A"]):
                print(f"    - {tier}")
        else:
            print("  N/A")

        print("\nSample embedding text:")
        print(sample.get("embedding_text", "N/A"))


if __name__ == "__main__":
    main()
