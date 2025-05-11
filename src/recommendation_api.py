import os
from openai import OpenAI
from dotenv import load_dotenv
# from vector_store import SimpleVectorStore

# Import the factory instead of directly importing SimpleVectorStore
from vector_store_factory import get_vector_store

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load vector store
vector_store = get_vector_store()
print(f"Loaded vector store with {len(vector_store.products)} products")


def get_embedding(text):
    """Generate embedding for a query using OpenAI's API"""
    try:
        response = client.embeddings.create(model="text-embedding-3-small", input=text)
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


def enhance_query_with_profile(query, user_profile=None):
    """Enhance the search query with profile information"""
    if not user_profile:
        return query

    # Start with the original query
    enhanced_query = query

    # Add key profile information to create a more detailed query
    profile_elements = []

    # Add job role and industry if available
    if user_profile.job_role:
        profile_elements.append(f"for a {user_profile.job_role}")
    if user_profile.industry:
        profile_elements.append(f"in the {user_profile.industry} industry")

    # Add common tasks if available
    if user_profile.common_tasks:
        tasks_text = ", ".join(
            [task.replace("_", " ") for task in user_profile.common_tasks[:3]]
        )
        profile_elements.append(f"who works on {tasks_text}")

    # Add improvement areas if available
    if user_profile.improvement_areas:
        areas_text = ", ".join(
            [area.replace("_", " ") for area in user_profile.improvement_areas[:3]]
        )
        profile_elements.append(f"looking to improve {areas_text}")

    # Add interests if available
    if user_profile.interests:
        interests_text = ", ".join(user_profile.interests[:3])
        profile_elements.append(f"interested in {interests_text}")

    # Add challenges if available
    if user_profile.challenges:
        challenges_text = ", ".join(user_profile.challenges[:3])
        profile_elements.append(f"facing challenges with {challenges_text}")

    # Add keywords from workflow description if available
    if user_profile.workflow_description:
        # Just add the workflow description directly since embeddings can handle it
        profile_elements.append(
            f"with workflow: {user_profile.workflow_description[:100]}"
        )

    # Add keywords from ideal solution if available
    if user_profile.ideal_solution:
        profile_elements.append(f"needs: {user_profile.ideal_solution[:100]}")

    # Combine everything into an enhanced query
    if profile_elements:
        enhanced_query = f"{query} {' '.join(profile_elements)}"

    print(f"Enhanced query: {enhanced_query}")
    return enhanced_query


def filter_by_budget(recommendations, budget_preference):
    """Filter recommendations based on budget preference"""
    if not budget_preference:
        return recommendations

    # Define budget tiers and which preference includes which tiers
    budget_tiers = {
        "free": ["free"],
        "freemium": ["free", "freemium"],
        "paid": ["free", "freemium", "paid"],
        "enterprise": ["free", "freemium", "paid", "enterprise"],
    }

    allowed_tiers = budget_tiers.get(
        budget_preference.lower(), ["free", "freemium", "paid", "enterprise"]
    )

    # Filter recommendations
    filtered_recommendations = []
    for rec in recommendations:
        # Check if product has budget_tier information
        product_tier = rec.get("budget_tier", "").lower()

        # If no budget tier info, include it by default
        if not product_tier or product_tier in allowed_tiers:
            filtered_recommendations.append(rec)

    return filtered_recommendations


def boost_relevant_products(recommendations, user_profile):
    """Boost scores for products that match specific user needs"""
    if not user_profile:
        return recommendations

    for rec in recommendations:
        boost_score = 0.0
        product = rec.get("product", {})

        # Boost for matching industry
        if user_profile.industry and "industries" in product:
            if user_profile.industry.lower() in [
                ind.lower() for ind in product["industries"]
            ]:
                boost_score += 0.05

        # Boost for matching company size
        if user_profile.company_size and "company_sizes" in product:
            if user_profile.company_size in product["company_sizes"]:
                boost_score += 0.05

        # Boost for matching interests
        if user_profile.interests and "tags" in product:
            matching_interests = sum(
                1
                for interest in user_profile.interests
                if any(interest.lower() in tag.lower() for tag in product["tags"])
            )
            boost_score += 0.02 * matching_interests

        # Boost for matching improvement areas
        if user_profile.improvement_areas and "features" in product:
            matching_areas = sum(
                1
                for area in user_profile.improvement_areas
                if any(
                    area.replace("_", " ").lower() in feature.lower()
                    for feature in product["features"]
                )
            )
            boost_score += 0.03 * matching_areas

        # Apply the boost
        rec["similarity_score"] = min(1.0, rec["similarity_score"] + boost_score)
        rec["boosted"] = boost_score > 0

    # Re-sort by updated similarity score
    recommendations.sort(key=lambda x: x["similarity_score"], reverse=True)

    return recommendations


def get_recommendations(query, user_profile=None, top_k=5):
    """Get product recommendations based on a query and user profile"""
    # Enhance the query with profile information
    enhanced_query = enhance_query_with_profile(query, user_profile)

    # Generate embedding for the enhanced query
    query_embedding = get_embedding(enhanced_query)
    if not query_embedding:
        return {"error": "Failed to generate embedding for query"}

    # Search for similar products
    results = vector_store.search(
        query_embedding, top_k=top_k * 2
    )  # Get more results for filtering

    # Format results
    recommendations = []
    for result in results:
        product = result["product"]
        recommendations.append(
            {
                "name": product["name"],
                "tagline": product["tagline"],
                "description": product.get(
                    "detailed_description", product.get("description", "")
                ),
                "website": product.get("website", ""),
                "similarity_score": result["similarity"],
                "budget_tier": product.get("pricing_tier", ""),
                "product": product,  # Include full product for filtering/boosting
            }
        )

    # Apply budget filtering if user has preference
    if user_profile and user_profile.budget_preference:
        recommendations = filter_by_budget(
            recommendations, user_profile.budget_preference
        )

    # Boost scores based on profile matching
    if user_profile:
        recommendations = boost_relevant_products(recommendations, user_profile)

    # Truncate to requested number
    recommendations = recommendations[:top_k]

    # Remove the full product data before returning
    for rec in recommendations:
        rec.pop("product", None)

    return {"recommendations": recommendations}


def main():
    """Interactive recommendation testing"""
    print("Product Recommendation System")
    print("Enter your query or type 'exit' to quit")

    while True:
        query = input("\nWhat kind of product are you looking for? ")
        if query.lower() == "exit":
            break

        results = get_recommendations(query)

        if "error" in results:
            print(f"Error: {results['error']}")
            continue

        print("\nRecommended Products:")
        for i, rec in enumerate(results["recommendations"]):
            print(f"\n{i + 1}. {rec['name']}")
            print(f"   {rec['tagline']}")
            print(f"   Similarity: {rec['similarity_score']:.4f}")
            print(f"   Website: {rec['website']}")


if __name__ == "__main__":
    main()
