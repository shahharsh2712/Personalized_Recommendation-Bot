# Personalized Product Recommendation System

A system that enriches product data, generates embeddings, and provides personalized recommendations via email using OpenAI embeddings and MongoDB.

## Project Overview

This system:

1. Enriches product data using Perplexity API.
2. Generates embeddings using OpenAI's embedding model.
3. Stores enriched products and embeddings in MongoDB.
4. Delivers personalized recommendations via email.

## Setup

### Prerequisites

- Python 3.8+
- OpenAI API key
- Perplexity API key
- MongoDB (local or remote)
- SendGrid API key (for email delivery)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/personalized-recommendations.git
   cd personalized-recommendations
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API keys and configuration:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   PERPLEXITY_API_KEY=your_perplexity_api_key
   MONGODB_URI=mongodb://localhost:27017/
   RECOMMENDATION_DB_NAME=app_recommendations
   SENDGRID_API_KEY=your_sendgrid_api_key
   SENDER_EMAIL=your_email@example.com
   SENDER_NAME=App Recommendations
   ```

## Usage

### Data Enrichment

```bash
python src/perplexity_enrich_products.py
```

### Generate Embeddings

```bash
python src/generate_embeddings.py
```

### Send Recommendation Emails

```bash
python src/email_sender.py
```

## Project Structure

- `src/` - Source code
  - `perplexity_enrich_products.py` - Enriches product data using Perplexity API
  - `generate_embeddings.py` - Generates embeddings for products
  - `email_sender.py` - Sends personalized recommendation emails
- `data/` - Data files
  - `products.json` - Original product data
  - `enriched_products.json` - Products enriched with Perplexity API
  - `products_with_embeddings.json` - Products with embeddings
- `templates/` - Email templates
- `storage/` - Database connection and models
- `delivery/` - Email delivery functionality
- `users/` - User profile management
- `recommender/` - Recommendation logic

## Contributing

Feel free to open issues or submit pull requests for improvements or bug fixes.

## License

This project is licensed under the MIT License.
