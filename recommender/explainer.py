import os
import logging
import random
from dotenv import load_dotenv
from openai import OpenAI
import json
import re

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RecommendationExplainer:
    """Generates detailed explanations for why products were recommended"""

    def __init__(self):
        # Initialize OpenAI client if API key is available
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.use_ai = bool(self.openai_api_key)

        if self.use_ai:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            logger.info("AI-powered explanations enabled")
        else:
            logger.info("Using template-based explanations (AI disabled)")

    def generate_explanation(self, user, product, similarity_score):
        """Generate a detailed explanation for why this product was recommended"""
        if self.use_ai:
            return self._generate_ai_explanation(user, product, similarity_score)
        else:
            return self._generate_template_explanation(user, product, similarity_score)

    def _generate_ai_explanation(self, user, product, similarity_score):
        """Generate an AI-powered explanation using OpenAI"""
        try:
            # Extract user preferences
            preferences = user.get("preferences", {})
            user_name = user.get("name", "").split()[0]  # First name

            # Create a context string for the AI
            context = self._create_explanation_context(
                user_name, preferences, product, similarity_score
            )

            # Generate explanation using OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at explaining product recommendations in a personalized, helpful way. Your explanations are concise (40-60 words), friendly, and highlight the specific aspects of the product that match the user's needs and preferences.",
                    },
                    {"role": "user", "content": context},
                ],
                max_tokens=150,
                temperature=0.7,
            )

            explanation = response.choices[0].message.content.strip()
            return explanation

        except Exception as e:
            logger.error(f"Error generating AI explanation: {e}")
            # Fall back to template explanation
            return self._generate_template_explanation(user, product, similarity_score)

    def _create_explanation_context(
        self, user_name, preferences, product, similarity_score
    ):
        """Create a context string for AI explanation generation"""
        context = f"Please explain to {user_name} why the product '{product['name']}' was recommended.\n\n"

        context += "Product Information:\n"
        context += f"- Name: {product['name']}\n"
        context += f"- Tagline: {product['tagline']}\n"
        context += f"- Categories: {', '.join(product.get('categories', []))}\n"
        if product.get("description"):
            context += f"- Description: {product['description']}\n"

        context += "\nUser Preferences:\n"
        if preferences.get("interests"):
            context += f"- Interests: {', '.join(preferences['interests'])}\n"
        if preferences.get("preferred_categories"):
            context += f"- Preferred Categories: {', '.join(preferences['preferred_categories'])}\n"
        if preferences.get("profession"):
            context += f"- Profession: {preferences['profession']}\n"
        if preferences.get("favorite_tools"):
            context += f"- Favorite Tools: {', '.join(preferences['favorite_tools'])}\n"
        if preferences.get("goals"):
            context += f"- Goals: {', '.join(preferences['goals'][:2])}\n"
        if preferences.get("pain_points"):
            context += f"- Pain Points: {', '.join(preferences['pain_points'][:2])}\n"

        context += f"\nSimilarity Score: {similarity_score * 100:.1f}%\n"
        context += "\nGenerate a personalized explanation for why this product was recommended to the user."

        return context

    def _generate_template_explanation(self, user, product, similarity_score):
        """Generate a template-based explanation without AI"""
        templates = [
            "Based on your {preference_type}, {product_name} seems like a great fit for your needs.",
            "{product_name} aligns well with your interest in {matched_interest}.",
            "As someone interested in {matched_interest}, you might find {product_name} particularly useful.",
            "We noticed your preference for {matched_preference} and thought {product_name} would be relevant.",
            "{product_name} is popular among {profession_type} professionals like yourself.",
            "This tool could help with your goal to {matched_goal}.",
            "Many {profession_type} professionals use {product_name} to enhance their workflow.",
        ]

        preferences = user.get("preferences", {})

        # Get potential matches
        matched_interest = (
            random.choice(preferences.get("interests", ["relevant topics"]))
            if preferences.get("interests")
            else "productivity"
        )
        matched_category = (
            random.choice(preferences.get("preferred_categories", ["useful apps"]))
            if preferences.get("preferred_categories")
            else "productivity tools"
        )
        profession = preferences.get("profession", "busy")
        matched_goal = (
            random.choice(preferences.get("goals", ["improve your workflow"]))
            if preferences.get("goals")
            else "improve your workflow"
        )

        # Pick template and format
        template = random.choice(templates)

        explanation = template.format(
            preference_type=random.choice(["preferences", "interests", "profile"]),
            product_name=product["name"],
            matched_interest=matched_interest,
            matched_preference=random.choice([matched_interest, matched_category]),
            profession_type=profession,
            matched_goal=matched_goal,
        )

        # Add confidence statement based on similarity score
        if similarity_score > 0.8:
            explanation += f" This is a very strong match for your preferences."
        elif similarity_score > 0.6:
            explanation += f" This matches your preferences quite well."

        return explanation

    def batch_explain_recommendations(self, user, recommendations):
        """Generate explanations for a batch of recommendations"""
        explained_recommendations = []

        for rec in recommendations:
            similarity = rec.get("confidence", 50) / 100
            explanation = self.generate_explanation(user, rec, similarity)

            # Update the recommendation with the explanation
            rec_copy = rec.copy()
            rec_copy["detailed_explanation"] = explanation
            explained_recommendations.append(rec_copy)

        return explained_recommendations

    def batch_llm_rerank_and_reason(self, user, candidates, top_k=5):
        """Use LLM to rerank and generate reasons for candidate apps based on chip-based preferences."""
        preferences = user.get("preferences", {})
        pain_points = preferences.get("pain_points", [])
        platforms = preferences.get("platforms", [])
        budget = preferences.get("budget_pref", None)
        cadence = preferences.get("cadence", None)
        user_name = user.get("name", "User")

        # Prepare JSON for LLM
        candidate_json = [
            {
                "name": app["name"],
                "tagline": app.get("tagline", ""),
                "description": app.get("description", ""),
                "platforms": app.get("platforms", []),
                "pricing": app.get("pricing", ""),
            }
            for app in candidates
        ]

        prompt = f"""
You are an app recommendation assistant.
User: {user_name}
Pain points: {", ".join(pain_points) if pain_points else "None"}
Preferred platforms: {", ".join(platforms) if platforms else "Any"}
Budget: {budget or "Any"}
Cadence: {cadence or "Any"}
Below are {len(candidate_json)} candidate apps (in JSON).
Pick the {top_k} most relevant and, for each, write one sentence (<30 words) explaining why it helps the user.
Respond in JSON: [{{name, reason}}].

Candidate apps:
{candidate_json}
"""
        if self.use_ai:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert at app recommendations. Be concise, specific, and user-focused.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=500,
                    temperature=0.7,
                )

                # Try to parse the JSON from the LLM response
                content = response.choices[0].message.content.strip()
                logger.info(f"Raw LLM response content: {content}")
                # Remove code block markers if present
                if content.startswith("```"):
                    content = content.split("```", 1)[-1].strip()
                if content.lower().startswith("json"):
                    content = content[4:].strip()
                # Find the first [ and last ] to extract the JSON array
                start = content.find("[")
                end = content.rfind("]") + 1
                json_str = content[start:end]
                # Remove trailing commas before closing bracket
                json_str = re.sub(r",\s*\]", "]", json_str)
                result = json.loads(json_str)
                # result: list of {name, reason}
                # Deduplicate by name, keep first occurrence
                seen = set()
                deduped_result = []
                for item in result:
                    if item["name"] not in seen:
                        deduped_result.append(item)
                        seen.add(item["name"])
                # Map back to full app info
                name_to_app = {app["name"]: app for app in candidates}
                recommendations = []
                for item in deduped_result:
                    app = name_to_app.get(item["name"])
                    if app:
                        app_copy = app.copy()
                        app_copy["reason"] = item["reason"]
                        recommendations.append(app_copy)
                return recommendations[:top_k]
            except Exception as e:
                logger.error(f"LLM rerank/reason failed: {e}")
                # Fallback to template
        # Fallback: template-based reason
        recommendations = []
        for app in candidates[:top_k]:
            reason = self._template_chip_reason(user, app)
            app_copy = app.copy()
            app_copy["reason"] = reason
            recommendations.append(app_copy)
        return recommendations

    def _template_chip_reason(self, user, app):
        """Generate a template-based reason using chip-based fields."""
        preferences = user.get("preferences", {})
        pain_points = preferences.get("pain_points", [])
        platforms = preferences.get("platforms", [])
        budget = preferences.get("budget_pref", None)
        parts = []
        if pain_points:
            for pain in pain_points:
                if pain.lower() in app.get("description", "").lower():
                    parts.append(f"Helps with: {pain}")
                    break
        if platforms:
            app_platforms = app.get("platforms", [])
            overlap = set(platforms) & set(app_platforms)
            if overlap:
                parts.append(f"Works on your platform: {', '.join(list(overlap))}")
        if budget == "free-only" and app.get("pricing", "") in ["free", "freemium"]:
            parts.append("Free or freemium app")
        if not parts:
            parts.append("Matches your preferences")
        return "; ".join(parts)


# Example usage
if __name__ == "__main__":
    explainer = RecommendationExplainer()

    # Sample data for testing
    test_user = {
        "name": "John Smith",
        "preferences": {
            "interests": ["productivity", "automation", "time management"],
            "preferred_categories": ["Productivity", "AI Tools"],
            "profession": "Developer",
            "goals": ["automate repetitive tasks", "learn new technologies"],
        },
    }

    test_product = {
        "name": "TaskMaster Pro",
        "tagline": "AI-powered task management for developers",
        "description": "TaskMaster helps developers automate workflow and save time.",
        "categories": ["Productivity", "Developer Tools"],
    }

    # Generate explanation
    explanation = explainer.generate_explanation(test_user, test_product, 0.85)
    print("Generated explanation:")
    print(explanation)
