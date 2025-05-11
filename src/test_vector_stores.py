import json
import numpy as np
import time
import os
from openai import OpenAI
from dotenv import load_dotenv
from vector_store import SimpleVectorStore
from improved_vector_store import ImprovedVectorStore
from vector_store_factory import get_vector_store

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


def compare_search_performance():
    """Compare performance between original and improved vector stores"""
    # Load both stores
    print("Loading original vector store...")
    original_store = SimpleVectorStore.load("data/vector_store.pkl")

    print("Loading improved vector store...")
    improved_store = get_vector_store(use_improved=True)

    # Test queries
    test_queries = [
        "task management software for remote teams",
        "AI image generation tool for marketing",
        "analytics dashboard for e-commerce businesses",
        "email marketing automation platform",
        "project management with kanban boards",
    ]

    # Generate embeddings for queries
    query_embeddings = []
    for query in test_queries:
        embedding = generate_embedding(query)
        if embedding:
            query_embeddings.append(embedding)

    # Test original store
    print("\nTesting original vector store...")
    original_times = []
    for i, embedding in enumerate(query_embeddings):
        start = time.time()
        results = original_store.search(embedding, top_k=5)
        end = time.time()
        original_times.append(end - start)

        print(f"\nQuery: {test_queries[i]}")
        print(f"Search time: {original_times[-1]:.4f} seconds")
        print("Top result: " + results[0]["product"]["name"])

    # Test improved store
    print("\nTesting improved vector store...")
    improved_times = []
    for i, embedding in enumerate(query_embeddings):
        start = time.time()
        results = improved_store.search(embedding, top_k=5)
        end = time.time()
        improved_times.append(end - start)

        print(f"\nQuery: {test_queries[i]}")
        print(f"Search time: {improved_times[-1]:.4f} seconds")
        print("Top result: " + results[0]["product"]["name"])

    # Compare times
    avg_original = sum(original_times) / len(original_times)
    avg_improved = sum(improved_times) / len(improved_times)

    print("\n=== Performance Comparison ===")
    print(f"Original store average search time: {avg_original:.4f} seconds")
    print(f"Improved store average search time: {avg_improved:.4f} seconds")

    if avg_improved < avg_original:
        speedup = avg_original / avg_improved
        print(f"The improved store is {speedup:.2f}x faster")
    else:
        print(
            "The original store is faster in this test (unusual, might be due to small dataset)"
        )


if __name__ == "__main__":
    compare_search_performance()
