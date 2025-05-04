import os
from bson import ObjectId
from flask import Blueprint, jsonify, request, current_app
from flask_pymongo import PyMongo
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from .middleware import api_key_required

# Global variable to store mongo instance
mongo = None


def set_mongo(mongo_instance):
    global mongo
    mongo = mongo_instance


def login():
    global mongo
    if mongo is None:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Database connection not initialized",
                    "code": 500,
                }
            ),
            500,
        )

    email = request.json.get("email")
    password = request.json.get("password")

    # Input validation
    if not email or not password:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Email and password are required",
                    "code": 400,
                }
            ),
            400,
        )

    # Mencari pengguna di database
    user = mongo.db.users.find_one({"email": email})
    if not user:
        return (
            jsonify({"status": "error", "message": "User not found", "code": 404}),
            404,
        )

    # Verifikasi password
    if not check_password_hash(user["password"], password):
        return (
            jsonify({"status": "error", "message": "Invalid credentials", "code": 401}),
            401,
        )

    # Membuat access token
    access_token = create_access_token(identity=str(user["_id"]))
    refresh_token = create_refresh_token(identity=str(user["_id"]))

    # Kembalikan data dalam response
    return (
        jsonify(
            {
                "status": "success",
                "message": "Login successful",
                "data": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {
                        "id": str(user["_id"]),
                        "email": user["email"],
                        "username": user["username"],
                    },
                    "api_key": os.getenv("API_KEY"),
                },
                "code": 200,
            }
        ),
        200,
    )


def register(mongo):
    username = request.json.get("username")
    email = request.json.get("email")
    password = request.json.get("password")

    # Input validation
    if not username or not password or not email:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Email, Username, and Password are required",
                    "code": 400,
                }
            ),
            400,
        )

    # Validate email format
    import re

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return (
            jsonify(
                {"status": "error", "message": "Invalid email format", "code": 400}
            ),
            400,
        )

    # Memeriksa apakah email sudah ada
    if mongo.db.users.find_one({"email": email}):
        return (
            jsonify({"status": "error", "message": "User already exists", "code": 409}),
            409,
        )

    # Meng-hash password
    hashed_password = generate_password_hash(password)

    # Menyimpan pengguna baru ke database
    new_user = {
        "email": email,
        "username": username,
        "password": hashed_password,
        "api_key": os.getenv("API_KEY"),
    }
    result = mongo.db.users.insert_one(new_user)

    return (
        jsonify(
            {
                "status": "success",
                "message": "Registration successful",
                "data": {
                    "user_id": str(result.inserted_id),
                    "username": username,
                    "email": email,
                },
                "code": 201,
            }
        ),
        201,
    )


def login_with_mongo(mongo):
    email = request.json.get("email")
    password = request.json.get("password")

    # Input validation
    if not email or not password:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Email and password are required",
                    "code": 400,
                }
            ),
            400,
        )

    user = mongo.db.users.find_one({"email": email})
    if not user:
        return (
            jsonify({"status": "error", "message": "User not found", "code": 404}),
            404,
        )

    # Cek password pakai check_password_hash
    if not check_password_hash(user["password"], password):
        return (
            jsonify({"status": "error", "message": "Invalid credentials", "code": 401}),
            401,
        )

    # Set token expiration to 2 days
    access_token = create_access_token(
        identity=str(user["_id"]), expires_delta=timedelta(days=2)
    )
    return (
        jsonify(
            {
                "status": "success",
                "message": "Login successful",
                "data": {
                    "access_token": access_token,
                    "user": {"id": str(user["_id"]), "email": user["email"]},
                },
                "code": 200,
            }
        ),
        200,
    )


@jwt_required()
def profile():
    current_user_id = get_jwt_identity()
    user = mongo.db.users.find_one({"_id": ObjectId(current_user_id)})

    if not user:
        return (
            jsonify({"status": "error", "message": "User not found", "code": 404}),
            404,
        )

    return (
        jsonify(
            {
                "status": "success",
                "message": "Profile retrieved successfully",
                "data": {"username": user["username"], "email": user["email"]},
                "code": 200,
            }
        ),
        200,
    )


@jwt_required(refresh=True)
def refresh_token():
    identity = get_jwt_identity()
    # Set refresh token expiration to 2 days
    new_access_token = create_access_token(
        identity=identity, expires_delta=timedelta(days=2)
    )
    return (
        jsonify(
            {
                "status": "success",
                "message": "Token refreshed successfully",
                "data": {"access_token": new_access_token},
                "code": 200,
            }
        ),
        200,
    )


def init_auth_routes(app, mongo_instance):
    global mongo
    mongo = mongo_instance

    api_auth = Blueprint("api_auth", __name__, url_prefix="/api/auth")

    @api_auth.route("/register", methods=["POST"])
    def blueprint_register():
        return register(mongo)

    @api_auth.route("/login", methods=["POST"])
    def blueprint_login():
        return login()

    @api_auth.route("/profile", methods=["GET"])
    @jwt_required()
    @api_key_required
    def blueprint_profile():
        return profile()

    @api_auth.route("/refresh", methods=["POST"])
    @jwt_required(refresh=True)
    @api_key_required
    def blueprint_refresh_token():
        return refresh_token()

    return api_auth
