import os
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt
from flask import Flask, jsonify, render_template, request, g

app = Flask(__name__)

DATABASE = "users.db"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 2


def get_secret_key():
    """Read the JWT secret from an environment variable."""
    secret = os.getenv("JWT_SECRET")

    if not secret:
        raise RuntimeError(
            "JWT_SECRET is not set. Add it as an environment variable/secret."
        )

    return secret


def get_db():
    """Open one SQLite connection for the current request."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row

    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    """Close the database connection after each request."""
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    """Create the users table if it does not already exist."""
    db = sqlite3.connect(DATABASE)

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
        """
    )

    db.commit()
    db.close()


def valid_email(email):
    """Basic email-format validation."""
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return re.match(pattern, email) is not None


def create_token(user_id):
    """Create a JWT that expires after two hours."""
    now = datetime.now(timezone.utc)

    payload = {
        "user_id": user_id,
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRATION_HOURS),
    }

    return jwt.encode(
        payload,
        get_secret_key(),
        algorithm=JWT_ALGORITHM
    )


def token_required(route_function):
    """Protect an API route with a Bearer JWT."""

    @wraps(route_function)
    def wrapper(*args, **kwargs):

        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({
                "success": False,
                "message": "Authorization header with Bearer token is required."
            }), 401

        token = auth_header.split(" ", 1)[1].strip()

        if not token:
            return jsonify({
                "success": False,
                "message": "JWT token is missing."
            }), 401

        try:
            payload = jwt.decode(
                token,
                get_secret_key(),
                algorithms=[JWT_ALGORITHM]
            )

            user_id = payload.get("user_id")

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "Invalid token payload."
                }), 401

            g.user_id = user_id

        except jwt.ExpiredSignatureError:
            return jsonify({
                "success": False,
                "message": "Token has expired. Please log in again."
            }), 401

        except jwt.InvalidTokenError:
            return jsonify({
                "success": False,
                "message": "Invalid JWT token."
            }), 401

        return route_function(*args, **kwargs)

    return wrapper


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json(silent=True) or {}

    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    # Check required fields
    if not username or not email or not password:
        return jsonify({
            "success": False,
            "message": "Username, email and password are required."
        }), 400

    # Validate email
    if not valid_email(email):
        return jsonify({
            "success": False,
            "message": "Please enter a valid email address."
        }), 400

    # Validate password length
    if len(password) < 6:
        return jsonify({
            "success": False,
            "message": "Password must be at least 6 characters long."
        }), 400

    db = get_db()

    # Check duplicate email
    existing_user = db.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    if existing_user:
        return jsonify({
            "success": False,
            "message": "An account with this email already exists."
        }), 409

    # Hash password using bcrypt
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    # Store only the hash
    db.execute(
        """
        INSERT INTO users (username, email, password_hash)
        VALUES (?, ?, ?)
        """,
        (username, email, password_hash)
    )

    db.commit()

    return jsonify({
        "success": True,
        "message": "Registration successful. You can now log in."
    }), 201


@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required."
        }), 400

    db = get_db()

    user = db.execute(
        """
        SELECT id, username, email, password_hash
        FROM users
        WHERE email = ?
        """,
        (email,)
    ).fetchone()

    if not user:
        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    # Compare entered password with stored bcrypt hash
    password_matches = bcrypt.checkpw(
        password.encode("utf-8"),
        user["password_hash"].encode("utf-8")
    )

    if not password_matches:
        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    # Create JWT
    token = create_token(user["id"])

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "token": token
    }), 200


@app.route("/api/profile", methods=["GET"])
@token_required
def profile():

    db = get_db()

    user = db.execute(
        """
        SELECT id, username, email
        FROM users
        WHERE id = ?
        """,
        (g.user_id,)
    ).fetchone()

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404

    return jsonify({
        "success": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }
    }), 200


@app.errorhandler(404)
def not_found(error):

    if request.path.startswith("/api/"):
        return jsonify({
            "success": False,
            "message": "API endpoint not found."
        }), 404

    return "Page not found.", 404


@app.errorhandler(500)
def internal_error(error):

    if request.path.startswith("/api/"):
        return jsonify({
            "success": False,
            "message": "Internal server error."
        }), 500

    return "Internal server error.", 500


# Create database/table when application starts
init_db()


if __name__ == "__main__":

    port = int(os.getenv("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )