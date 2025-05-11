# AI-Powered Product Recommendation System

A semantic search-based recommendation system for software products using OpenAI embeddings and Perplexity API for data enrichment.

## Project Overview

This system helps users find relevant software products based on their specific needs by:

1. Enriching product data using Perplexity API
2. Generating embeddings using OpenAI's embedding model
3. Creating a vector store for semantic search
4. Providing recommendations through a simple API and web interface

## Setup

### Prerequisites

- Python 3.8+
- OpenAI API key
- Perplexity API key

### Installation

1. Clone the repository
   \\\
   git clone https://github.com/yourusername/product-recommendation-system.git
   cd product-recommendation-system
   \\\

2. Install dependencies
   \\\
   pip install -r requirements.txt
   \\\

3. Create a .env file with your API keys
   \\\
   OPENAI_API_KEY=your_openai_api_key
   PERPLEXITY_API_KEY=your_perplexity_api_key
   \\\

## Usage

### Data Enrichment

\\\
python src/perplexity_enrich_products.py
\\\

### Generate Embeddings

\\\
python src/generate_embeddings.py
\\\

### Create Vector Store

\\\
python src/create_vector_store.py
\\\

### Run Recommendation API

\\\
python src/recommendation_api.py
\\\

### Run Web Interface

\\\
python src/web_app.py
\\\

## Project Structure

- \src/\ - Source code
  - \perplexity_enrich_products.py\ - Enriches product data using Perplexity API
  - \generate_embeddings.py\ - Generates embeddings for products
  - \ector_store.py\ - Vector store implementation
  - \create_vector_store.py\ - Creates the vector store
  - \
    ecommendation_api.py\ - Recommendation API implementation
  - \web_app.py\ - Web interface for the recommendation system
- \data/\ - Data files
  - \products.json\ - Original product data
  - \enriched_products.json\ - Products enriched with Perplexity API
  - \products_with_embeddings.json\ - Products with embeddings
