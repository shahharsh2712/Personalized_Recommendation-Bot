import secrets
import hashlib
from datetime import datetime, timedelta

# Simple in-memory session store (should be replaced with Redis or database in production)
active_sessions = {}


def hash_password(password, salt=None):
    """Hash a password for storage."""
    if salt is None:
        salt = secrets.token_hex(16)

    # Create hash
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,  # Number of iterations
    )

    return f"{salt}:{key.hex()}"


def verify_password(stored_password, provided_password):
    """Verify a password against its stored hash."""
    salt, key = stored_password.split(":")
    return stored_password == hash_password(provided_password, salt)


def generate_session_token():
    """Generate a session token."""
    return secrets.token_hex(32)


def create_session(user_id, expires_in_days=7):
    """Create a new session for a user."""
    token = generate_session_token()
    expires_at = datetime.now() + timedelta(days=expires_in_days)

    active_sessions[token] = {"user_id": user_id, "expires_at": expires_at}

    return token


def validate_session(token):
    """Validate a session token."""
    if token not in active_sessions:
        return None

    session = active_sessions[token]
    if session["expires_at"] < datetime.now():
        del active_sessions[token]
        return None

    return session["user_id"]


def end_session(token):
    """End a session."""
    if token in active_sessions:
        del active_sessions[token]
        return True
    return False
