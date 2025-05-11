import os
import logging
import random
from dotenv import load_dotenv
from openai import OpenAI

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
