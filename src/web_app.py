import os
import sys

from dotenv import load_dotenv

# Load .env from project root and run with src as working directory
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SRC_DIR)
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
os.chdir(SRC_DIR)
sys.path.insert(0, SRC_DIR)

from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    redirect,
    url_for,
    make_response,
)
from recommendation_api import get_recommendations
from models.user_profile import UserProfile
from repositories.user_repository import UserRepository
from mongo_sync import sync_profile_to_mongodb
import auth
from datetime import datetime
import json
from openai import OpenAI

app = Flask(
    __name__,
    template_folder="templates",  # Look for templates in the 'templates' folder
    static_folder="static",  # Look for static files in the 'static' folder
)
app.secret_key = os.urandom(24)  # Generate a random secret key

# Initialize user repository
user_repository = UserRepository()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Authentication middleware
def get_current_user():
    """Get the current logged-in user."""
    token = request.cookies.get("session_token")
    if not token:
        return None

    user_id = auth.validate_session(token)
    if not user_id:
        return None

    return user_repository.get_profile(user_id)


# Original route now checks for logged-in user
@app.route("/")
def index():
    user = get_current_user()
    if user:
        # Logged in users get the personalized version (we'll create this later)
        return redirect(url_for("dashboard"))
    else:
        # Anonymous users get the current search template
        return render_template("search.html")


# Authentication routes
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").lower()
        password = request.form.get("password", "")

        user_data = user_repository.get_user_by_email(email)
        if not user_data or not auth.verify_password(
            user_data["password_hash"], password
        ):
            return render_template("login.html", error="Invalid email or password")

        # Create session and set cookie
        token = auth.create_session(user_data["user_id"])

        profile = user_repository.get_profile(user_data["user_id"])
        next_url = (
            "profile_setup"
            if profile and profile.assessment_completeness < 30
            else "dashboard"
        )
        response = make_response(redirect(url_for(next_url)))
        response.set_cookie(
            "session_token", token, httponly=True, max_age=60 * 60 * 24 * 7
        )  # 7 days
        return response

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "")
        email = request.form.get("email", "").lower()
        password = request.form.get("password", "")

        # Validate inputs
        if not name or not email or not password:
            return render_template("signup.html", error="All fields are required")

        if user_repository.get_user_by_email(email):
            return render_template("signup.html", error="Email already in use")

        # Create user
        password_hash = auth.hash_password(password)
        try:
            user_id = user_repository.create_user(email, password_hash, name)

            sync_profile_to_mongodb(user_repository.get_profile(user_id))

            token = auth.create_session(user_id)

            # Redirect to profile setup
            response = make_response(redirect(url_for("profile_setup")))
            response.set_cookie(
                "session_token", token, httponly=True, max_age=60 * 60 * 24 * 7
            )  # 7 days
            return response
        except Exception as e:
            return render_template(
                "signup.html", error=f"Error creating account: {str(e)}"
            )

    return render_template("signup.html")


@app.route("/logout")
def logout():
    token = request.cookies.get("session_token")
    if token:
        auth.end_session(token)

    response = make_response(redirect(url_for("index")))
    response.delete_cookie("session_token")
    return response


@app.route("/profile/setup", methods=["GET", "POST"])
def profile_setup():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        # Process the form submission
        profile_data = {
            # Existing fields
            "job_role": request.form.get("job_role", ""),
            "industry": request.form.get("industry", ""),
            "company_size": request.form.get("company_size", ""),
            "interests": [
                x.strip()
                for x in request.form.get("interests", "").split(",")
                if x.strip()
            ],
            "tools_used": [
                x.strip()
                for x in request.form.get("tools_used", "").split(",")
                if x.strip()
            ],
            "challenges": [
                x.strip()
                for x in request.form.get("challenges", "").split(",")
                if x.strip()
            ],
            "budget_preference": request.form.get("budget_preference", ""),
            # New fields
            "common_tasks": request.form.getlist("common_tasks"),
            "improvement_areas": request.form.getlist("improvement_areas"),
            "workflow_description": request.form.get("workflow_description", ""),
            "ideal_solution": request.form.get("ideal_solution", ""),
        }

        # Calculate profile completeness
        possible_fields = 11  # Count of main profile fields
        filled_fields = sum(
            1
            for field, value in profile_data.items()
            if value and field != "recommendation_history"
        )
        profile_data["assessment_completeness"] = int(
            (filled_fields / possible_fields) * 100
        )

        user_repository.update_profile(user.user_id, profile_data)
        updated = user_repository.get_profile(user.user_id)
        sync_profile_to_mongodb(updated)

        return redirect(url_for("dashboard"))

    return render_template("profile_setup.html")


@app.route("/dashboard")
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    # Pass the user profile to the dashboard template
    return render_template("dashboard.html", user=user)


# API endpoint works for both anonymous and logged-in users
@app.route("/api/recommendations")
def api_recommendations():
    query = request.args.get("query", "")
    if not query:
        return jsonify({"error": "Query parameter is required"})

    # Get user for personalization (if logged in)
    user = get_current_user()

    results = get_recommendations(query, user_profile=user)

    if "error" in results:
        return jsonify(results), 503

    if user and results.get("recommendations"):
        profile_data = {
            "recommendation_history": user.recommendation_history
            + [
                {
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "results": [r["name"] for r in results["recommendations"][:3]],
                }
            ]
        }
        user_repository.update_profile(user.user_id, profile_data)

    return jsonify(results)


# Add a new route for the chat page
@app.route("/chat")
def chat_page():
    user = get_current_user()
    return render_template("chat.html", user=user)


# API endpoint for chat
@app.route("/api/chat", methods=["POST"])
def chat_api():
    data = request.json
    user_message = data.get("message", "")
    history = data.get("history", [])

    if not user_message:
        return jsonify({"response": "Please enter a message."})

    # Get user for personalization (if logged in)
    user = get_current_user()

    # Determine if this is a follow-up question
    is_followup = len(history) > 1

    # Create system message with instructions
    system_message = """You are a helpful product discovery assistant named Scout. 
Your job is to help users find the right tools and software for their needs.
When responding:
1. Be concise and friendly
2. Use bullet points where appropriate
3. Highlight key features and benefits
4. Suggest which tool might be best and why
5. Format your response in a clear, readable way
6. Include the original website links in your response

For follow-up questions, refer to the products mentioned in the previous responses.
If the user is asking about specific features, pricing, or comparisons of products 
you've already mentioned, focus on answering those specific questions.
"""

    # Create the conversation
    messages = [
        {"role": "system", "content": system_message},
    ]

    # Process conversation history for context if this is a follow-up
    previous_context = ""
    last_products = []
    if is_followup:
        # First, extract product names and context from previous exchanges
        for msg in history:
            # Only process assistant messages for product extraction
            if msg.get("role") == "assistant":
                previous_context += msg.get("content", "") + "\n"
                # (We could add more sophisticated extraction of product names here)

        # Then add all the previous messages to the conversation
        # But limit to last 4 exchanges (8 messages) to avoid token limits
        start_idx = max(0, len(history) - 8)
        for msg in history[start_idx:-1]:  # Exclude current message
            if msg.get("role") in ["user", "assistant"]:
                messages.append(
                    {"role": msg.get("role"), "content": msg.get("content", "")}
                )

    # Get product recommendations based on the query
    results = get_recommendations(user_message, user_profile=user, top_k=3)

    if "error" in results:
        return jsonify(
            {"response": f"Sorry, I encountered an error: {results['error']}"}
        )

    # Format product recommendations for the prompt
    product_info = ""
    for i, product in enumerate(results["recommendations"], 1):
        product_info += f"{i}. {product['name']}: {product['tagline']}\n"
        desc = (product.get("description") or "")[:200]
        product_info += f"   {desc}...\n"
        product_info += f"   Website: {product['website']}\n\n"
        last_products.append(product["name"])

    # Customize prompt based on whether it's a follow-up question
    if is_followup:
        prompt = f"""
User follow-up query: {user_message}

Previously, we've discussed these products:
{previous_context}

I also found these potentially relevant products for this follow-up:
{product_info}

If the user is asking about products we've already discussed, focus on answering their specific question.
If they seem to be asking about a new topic, introduce these new products.
"""
    else:
        prompt = f"""
User query: {user_message}

Based on this query, I found these relevant products:
{product_info}

Please provide a helpful, concise response that recommends these tools to the user based on their query.
Explain briefly why each tool might be helpful and suggest which one(s) might be most relevant.
"""

    messages.append({"role": "user", "content": prompt})

    try:
        # Get response from OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=800,
        )

        assistant_response = response.choices[0].message.content

        if user and results.get("recommendations"):
            profile_data = {
                "recommendation_history": user.recommendation_history
                + [
                    {
                        "query": user_message,
                        "timestamp": datetime.now().isoformat(),
                        "results": [r["name"] for r in results["recommendations"][:3]],
                    }
                ]
            }
            user_repository.update_profile(user.user_id, profile_data)

        quick_replies = generate_quick_replies(
            user_message, results.get("recommendations", [])
        )

        return jsonify({"response": assistant_response, "quick_replies": quick_replies})

    except Exception as e:
        print(f"Error calling OpenAI: {str(e)}")
        return jsonify(
            {
                "response": "I'm sorry, I encountered an error while processing your request."
            }
        )


# API endpoint for feedback
@app.route("/api/feedback", methods=["POST"])
def chat_feedback():
    data = request.json
    feedback_type = data.get("type", "")  # "helpful" or "not_helpful"
    message_id = data.get("message_id", "")
    comments = data.get("comments", "")

    # Get user for attribution (if logged in)
    user = get_current_user()
    user_id = user.user_id if user else "anonymous"

    # Here you would typically store the feedback in a database
    # For now, we'll just print it to the console
    print(f"Feedback received: {feedback_type} for message {message_id}")
    print(f"From user: {user_id}")
    print(f"Comments: {comments}")

    # If you had a feedback collection in your database:
    # feedback_repository.save_feedback({
    #     "user_id": user_id,
    #     "message_id": message_id,
    #     "feedback_type": feedback_type,
    #     "comments": comments,
    #     "timestamp": datetime.now().isoformat()
    # })

    return jsonify({"status": "success"})


# Function to generate quick reply suggestions
def generate_quick_replies(query, recommendations):
    quick_replies = []

    # Add comparison question if there are multiple recommendations
    if len(recommendations) >= 2:
        quick_replies.append(
            f"Compare {recommendations[0]['name']} and {recommendations[1]['name']}"
        )

    # Add pricing question
    quick_replies.append("Which one is free or has a free plan?")

    # Add features question
    quick_replies.append("What are the key features?")

    # Add alternative question
    quick_replies.append("Are there any alternatives?")

    return quick_replies


if __name__ == "__main__":
    from setup_frontend_data import ensure_vector_store

    ensure_vector_store()
    print("Frontend running at http://127.0.0.1:5000")
    print("Flow: /signup -> /profile/setup -> /dashboard")
    app.run(debug=True, host="127.0.0.1", port=5000, use_reloader=False)
