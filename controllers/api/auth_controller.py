from bson import ObjectId
from flask import Blueprint, jsonify, request
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


def login(mongo):
    username = request.json.get("username")
    password = request.json.get("password")

    user = mongo.db.users.find_one({"username": username})
    if not user:
        return jsonify({"message": "Pengguna tidak ditemukan"}), 400

    # Cek password pakai check_password_hash
    if not check_password_hash(user["password"], password):
        return jsonify({"message": "Kredensial tidak valid"}), 400

    # Set token expiration to 2 days
    access_token = create_access_token(
        identity=str(user["_id"]), expires_delta=timedelta(days=2)
    )
    return jsonify({"access_token": access_token}), 200


def register(mongo):
    username = request.json.get("username")
    password = request.json.get("password")

    if not username or not password:
        return jsonify({"message": "Username dan password harus diisi"}), 400

    if mongo.db.users.find_one({"username": username}):
        return jsonify({"message": "Pengguna sudah ada"}), 400

    hashed_password = generate_password_hash(password)

    mongo.db.users.insert_one(
        {"username": username, "password": hashed_password, "api_key": None}
    )

    return jsonify({"message": "Registrasi berhasil"}), 201


def profile(mongo):
    current_user_id = get_jwt_identity()
    user = mongo.db.users.find_one({"_id": ObjectId(current_user_id)})

    if not user:
        return jsonify({"message": "Pengguna tidak ditemukan"}), 400

    return jsonify({"username": user["username"]}), 200


def init_auth_routes(app, mongo):
    api_auth = Blueprint("api_auth", __name__, url_prefix="/api/auth")

    @api_auth.route("/register", methods=["POST"])
    def blueprint_register():
        return register(mongo)

    @api_auth.route("/login", methods=["POST"])
    def blueprint_login():
        return login(mongo)

    @api_auth.route("/profile", methods=["GET"])
    @jwt_required()
    def blueprint_profile():
        return profile(mongo)

    @api_auth.route("/refresh", methods=["POST"])
    @jwt_required(refresh=True)
    def refresh_token():
        identity = get_jwt_identity()
        # Also set refresh token expiration to 2 days
        new_access_token = create_access_token(
            identity=identity, expires_delta=timedelta(days=2)
        )
        return jsonify({"message": "Refresh token", "access_token": new_access_token})

    return api_auth
