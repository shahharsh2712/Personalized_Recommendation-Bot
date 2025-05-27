from flask import Flask, render_template, request, redirect, url_for, flash, session
from personalized_recommendations.users.profile import UserProfileManager
from personalized_recommendations.users.constants import (
    PAIN_POINTS,
    PLATFORMS,
    CADENCE_OPTIONS,
    ROLES,
    INTERESTS,
    BUDGET_PREFS,
    CHANNEL_OPTIONS,
)
import os

app = Flask(__name__)
app.secret_key = "supersecret"  # Change this in production!

profile_manager = UserProfileManager()


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]

        # Create user with minimal initial preferences
        preferences = {
            "pain_points": [],
            "platforms": [],
            "role": None,
            "budget_pref": None,
            "cadence": "daily",
        }

        success = profile_manager.create_user(email, name, preferences)
        if success:
            session["user_email"] = email  # Log them in
            flash(
                "Registration successful! Let's personalize your experience.", "success"
            )
            return redirect(url_for("onboarding"))
        else:
            flash("Failed to register user.", "danger")
    return render_template("register.html")


@app.route("/profile/<email>")
def profile(email):
    if not session.get("user_email"):
        flash("Please log in to view your profile.", "warning")
        return redirect(url_for("login"))
    user = profile_manager.get_user(email)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("home"))
    return render_template("profile.html", user=user)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        user = profile_manager.get_user(email)
        if user:
            session["user_email"] = email
            flash("Login successful!", "success")
            return redirect(url_for("profile", email=email))
        else:
            flash("User not found. Please register first.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_email", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


@app.route("/profile/<email>/edit", methods=["GET", "POST"])
def edit_profile(email):
    if not session.get("user_email") or session.get("user_email") != email:
        flash("You can only edit your own profile.", "danger")
        return redirect(url_for("login"))
    user = profile_manager.get_user(email)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("home"))
    preferences = user.get("preferences", {})
    if request.method == "POST":
        preferences["pain_points"] = request.form.getlist("pain_points")
        preferences["platforms"] = request.form.getlist("platforms")
        preferences["budget_pref"] = (
            "free-only" if request.form.get("budget_pref") else None
        )
        preferences["cadence"] = request.form.get("cadence", "daily")
        success = profile_manager.update_preferences(email, preferences)
        if success:
            flash("Profile updated successfully!", "success")
            user = profile_manager.get_user(email)
            return render_template("success.html", user=user)
        else:
            flash("Failed to update profile.", "danger")
    return render_template(
        "edit_profile.html",
        user=user,
        pain_points=PAIN_POINTS,
        platforms=PLATFORMS,
        cadence_options=CADENCE_OPTIONS,
    )


@app.route("/onboarding")
def onboarding():
    """Show the onboarding form with chips."""
    if not session.get("user_email"):
        return redirect(url_for("login"))

    return render_template(
        "onboarding.html",
        roles=ROLES,
        interests=INTERESTS,
        platforms=PLATFORMS,
        budget_prefs=BUDGET_PREFS,
        cadence_options=CADENCE_OPTIONS,
        channel_options=CHANNEL_OPTIONS,
    )


@app.route("/onboarding/complete", methods=["POST"])
def complete_onboarding():
    """Handle onboarding form submission."""
    if not session.get("user_email"):
        return redirect(url_for("login"))

    email = session["user_email"]
    user = profile_manager.get_user(email)

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("login"))

    # Get form data
    preferences = {
        "role": request.form.get("role") or request.form.get("role_custom"),
        "goal": request.form.get("goal"),
        "pain_point": request.form.get("pain_point"),
        "interests": request.form.getlist("interests"),
        "platforms": request.form.getlist("platforms"),
        "budget_pref": request.form.get("budget_pref", "any"),
        "cadence": request.form.get("cadence", "daily"),
        "channel": request.form.get("channel", "email"),
    }

    # Update user preferences
    success = profile_manager.update_preferences(email, preferences)

    if success:
        flash("Preferences updated successfully!", "success")
        user = profile_manager.get_user(email)
        return render_template("success.html", user=user)
    else:
        flash("Failed to update preferences.", "danger")
        return redirect(url_for("onboarding"))


@app.route("/unsubscribe")
def unsubscribe():
    email = request.args.get("email")
    if not email:
        return "Invalid unsubscribe link.", 400
    user = profile_manager.get_user(email)
    if not user:
        return "User not found.", 404
    # Mark as unsubscribed
    profile_manager.store.update_user(email, {"$set": {"subscribed": False}})
    return render_template("unsubscribe.html", user=user)


if __name__ == "__main__":
    app.run(debug=True)
