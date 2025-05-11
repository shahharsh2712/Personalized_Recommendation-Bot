import json
import os
import time
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_embedding(text):
    """Generate embedding for a text using OpenAI's API"""
    try:
        response = client.embeddings.create(model="text-embedding-3-small", input=text)
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


def main():
    # Load enriched products
    with open("data/enriched_products.json", "r", encoding="utf-8") as f:
        products = json.load(f)

    print(f"Loaded {len(products)} enriched products")
    print("Generating embeddings...")

    products_with_embeddings = []
    for i, product in enumerate(products):
        print(
            f"Generating embedding for product {i + 1}/{len(products)}: {product['name']}"
        )

        # Generate embedding using the optimized embedding text
        if "embedding_text" in product:
            embedding = generate_embedding(product["embedding_text"])
            if embedding:
                product["embedding"] = embedding
                products_with_embeddings.append(product)
            else:
                print(f"Failed to generate embedding for {product['name']}")
        else:
            print(f"No embedding_text found for {product['name']}")

        # Respect API rate limits
        time.sleep(0.5)

    # Save products with embeddings
    with open("data/products_with_embeddings.json", "w", encoding="utf-8") as f:
        json.dump(products_with_embeddings, f, indent=2, ensure_ascii=False)

    print(
        f"Saved {len(products_with_embeddings)} products with embeddings to data/products_with_embeddings.json"
    )


if __name__ == "__main__":
    main()
