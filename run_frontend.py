"""Start the original Flask onboarding + recommendation UI."""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, SRC)

from setup_frontend_data import ensure_vector_store  # noqa: E402
from web_app import app  # noqa: E402

if __name__ == "__main__":
    ensure_vector_store()
    print("Frontend: http://127.0.0.1:5000")
    print("  Sign up:   http://127.0.0.1:5000/signup")
    print("  Profile:   http://127.0.0.1:5000/profile/setup")
    print("  Dashboard: http://127.0.0.1:5000/dashboard")
    # use_reloader=False: debug reloader breaks when cwd changes to src/
    app.run(debug=True, host="127.0.0.1", port=5000, use_reloader=False)
