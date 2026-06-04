import os
import sys

from dotenv import load_dotenv

from app_paths import PROJECT_ROOT

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
sys.path.insert(0, PROJECT_ROOT)
from embeddings.provider import generate_embedding  # noqa: E402

_vector_store = None


def _get_vector_store():
    global _vector_store
    if _vector_store is None:
        from setup_frontend_data import ensure_vector_store
        from vector_store_factory import get_vector_store

        ensure_vector_store()
        _vector_store = get_vector_store(use_improved=False)
        print(f"Loaded vector store with {len(_vector_store.products)} products")
    return _vector_store


def get_embedding(text):
    """Generate embedding for a search query."""
    return generate_embedding(text)


def enhance_query_with_profile(query, user_profile=None):
    """Enhance the search query with profile information"""
    if not user_profile:
        return query

    enhanced_query = query
    profile_elements = []

    if user_profile.job_role:
        profile_elements.append(f"for a {user_profile.job_role}")
    if user_profile.industry:
        profile_elements.append(f"in the {user_profile.industry} industry")

    if user_profile.common_tasks:
        tasks_text = ", ".join(
            [task.replace("_", " ") for task in user_profile.common_tasks[:3]]
        )
        profile_elements.append(f"who works on {tasks_text}")

    if user_profile.improvement_areas:
        areas_text = ", ".join(
            [area.replace("_", " ") for area in user_profile.improvement_areas[:3]]
        )
        profile_elements.append(f"looking to improve {areas_text}")

    if user_profile.interests:
        interests_text = ", ".join(user_profile.interests[:3])
        profile_elements.append(f"interested in {interests_text}")

    if user_profile.challenges:
        challenges_text = ", ".join(user_profile.challenges[:3])
        profile_elements.append(f"facing challenges with {challenges_text}")

    if user_profile.workflow_description:
        profile_elements.append(
            f"with workflow: {user_profile.workflow_description[:100]}"
        )

    if user_profile.ideal_solution:
        profile_elements.append(f"needs: {user_profile.ideal_solution[:100]}")

    if profile_elements:
        enhanced_query = f"{query} {' '.join(profile_elements)}"

    return enhanced_query


def filter_by_budget(recommendations, budget_preference):
    """Filter recommendations based on budget preference"""
    if not budget_preference:
        return recommendations

    budget_tiers = {
        "free": ["free"],
        "freemium": ["free", "freemium"],
        "paid": ["free", "freemium", "paid"],
        "enterprise": ["free", "freemium", "paid", "enterprise"],
    }

    allowed_tiers = budget_tiers.get(
        budget_preference.lower(), ["free", "freemium", "paid", "enterprise"]
    )

    filtered_recommendations = []
    for rec in recommendations:
        product_tier = rec.get("budget_tier", "").lower()
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

        if user_profile.industry and "industries" in product:
            if user_profile.industry.lower() in [
                ind.lower() for ind in product["industries"]
            ]:
                boost_score += 0.05

        if user_profile.company_size and "company_sizes" in product:
            if user_profile.company_size in product["company_sizes"]:
                boost_score += 0.05

        if user_profile.interests and "tags" in product:
            matching_interests = sum(
                1
                for interest in user_profile.interests
                if any(interest.lower() in tag.lower() for tag in product["tags"])
            )
            boost_score += 0.02 * matching_interests

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

        rec["similarity_score"] = min(1.0, rec["similarity_score"] + boost_score)
        rec["boosted"] = boost_score > 0

    recommendations.sort(key=lambda x: x["similarity_score"], reverse=True)
    return recommendations


def _keyword_fallback_search(query, top_k=5):
    """Search products by text match when OpenAI embeddings are unavailable."""
    vector_store = _get_vector_store()
    terms = [t.lower() for t in query.split() if len(t) > 2]
    if not terms:
        terms = [query.lower()]

    scored = []
    for product in vector_store.products:
        text = " ".join(
            [
                product.get("name", ""),
                product.get("tagline", ""),
                product.get("description", ""),
                product.get("detailed_description", ""),
                " ".join(product.get("topics", []) or []),
            ]
        ).lower()
        matches = sum(1 for term in terms if term in text)
        if matches:
            scored.append((product, matches / len(terms)))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [{"product": p, "similarity": score} for p, score in scored[: top_k * 2]]


def get_recommendations(query, user_profile=None, top_k=5):
    """Get product recommendations based on a query and user profile"""
    enhanced_query = enhance_query_with_profile(query, user_profile)
    query_embedding = get_embedding(enhanced_query)

    if query_embedding:
        vector_store = _get_vector_store()
        results = vector_store.search(query_embedding, top_k=top_k * 2)
    else:
        results = _keyword_fallback_search(enhanced_query, top_k=top_k)
        if not results:
            return {
                "error": "Could not generate recommendations. Check your OpenAI API key and billing."
            }

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
                "product": product,
            }
        )

    if user_profile and user_profile.budget_preference:
        recommendations = filter_by_budget(
            recommendations, user_profile.budget_preference
        )

    if user_profile:
        recommendations = boost_relevant_products(recommendations, user_profile)

    recommendations = recommendations[:top_k]

    for rec in recommendations:
        rec.pop("product", None)

    return {"recommendations": recommendations}
