import os
import json
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API token
DEVELOPER_TOKEN = os.getenv("PRODUCT_HUNT_DEVELOPER_TOKEN")


def fetch_products(cursor=None, batch_size=20):
    """Fetch a batch of products from Product Hunt API using developer token"""
    url = "https://api.producthunt.com/v2/api/graphql"

    # Create cursor parameter if needed
    cursor_param = f', after: "{cursor}"' if cursor else ""

    # GraphQL query to fetch posts (products)
    query = f"""
    {{
      posts(first: {batch_size}{cursor_param}) {{
        pageInfo {{
          endCursor
          hasNextPage
        }}
        edges {{
          node {{
            id
            name
            tagline
            description
            topics {{
              edges {{
                node {{
                  name
                }}
              }}
            }}
            website
            votesCount
          }}
        }}
      }}
    }}
    """

    headers = {
        "Authorization": f"Bearer {DEVELOPER_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    }

    try:
        response = requests.post(url, json={"query": query}, headers=headers)

        if response.status_code == 200:
            return response.json().get("data", {}).get("posts")
        else:
            print(f"Error fetching products: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Exception when fetching products: {e}")
        return None


def process_products(products_data):
    """Process raw API data into clean product format"""
    if not products_data or "edges" not in products_data:
        print(f"Invalid product data format: {products_data}")
        return []

    processed = []

    for edge in products_data["edges"]:
        product = edge["node"]

        # Extract topics
        topics = []
        if product.get("topics") and product["topics"].get("edges"):
            topics = [edge["node"]["name"] for edge in product["topics"]["edges"]]

        # Clean product data
        processed_product = {
            "id": product["id"],
            "name": product["name"],
            "tagline": product["tagline"],
            "description": product.get("description", ""),
            "category": topics[0] if topics else "Uncategorized",
            "topics": topics,
            "website": product.get("website", ""),
            "votes_count": product.get("votesCount", 0),
        }

        processed.append(processed_product)

    return processed


def main():
    """Main function to fetch products from Product Hunt"""
    print("Fetching products from Product Hunt API using developer token...")

    if not DEVELOPER_TOKEN:
        print("Developer token not found. Please add it to your .env file.")
        return

    print(f"Using developer token: {DEVELOPER_TOKEN[:10]}...")

    all_products = []
    cursor = None
    has_next_page = True
    batch_size = 20
    target_count = 600  # Aim for slightly more to account for any filtering

    # Fetch products in batches
    while has_next_page and len(all_products) < target_count:
        print(f"Fetching batch of products (current count: {len(all_products)})")

        # Fetch a batch of products
        products_data = fetch_products(cursor, batch_size)

        if not products_data:
            print("Error fetching products. Stopping.")
            break

        # Process and add to our collection
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

        print(f"Fetched {len(processed_batch)} products in this batch")

    # Trim to target size if needed
    if len(all_products) > 500:
        all_products = all_products[:500]

    print(f"Successfully collected {len(all_products)} products")

    # Save to JSON file
    with open("data/products.json", "w", encoding="utf-8") as f:
        json.dump(all_products, f, indent=2, ensure_ascii=False)

    print(f"Saved products to data/products.json")

    # Show sample of the data
    print("\nSample Products:")
    for product in all_products[:3]:
        print(f"- {product['name']}: {product['tagline']}")


if __name__ == "__main__":
    main()
