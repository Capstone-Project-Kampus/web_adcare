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
    email = request.json.get("email")
    password = request.json.get("password")

    # Memeriksa apakah username, email, atau password kosong
    if not username or not password or not email:
        return jsonify({"msg": "Email, Username dan Password harus diisi"}), 400

    # Memeriksa apakah email sudah ada
    if mongo.db.users.find_one({"email": email}):
        return jsonify({"message": "Pengguna sudah ada"}), 400

    # Meng-hash password
    hashed_password = generate_password_hash(password)

    # Menyimpan pengguna baru ke database
    mongo.db.users.insert_one(
        {
            "email": email,
            "username": username,
            "password": hashed_password,
            "api_key": None,
        }
    )

    return jsonify({"msg": "Registrasi berhasil"}), 201


def login():
    email = request.json.get("email")
    password = request.json.get("password")

    # Mencari pengguna di database
    user = mongo.db.users.find_one({"email": email})
    if not user:
        return (
            jsonify({"msg": "Pengguna tidak ditemukan"}),
            401,
        )  # Ganti dengan 401 untuk kredensial yang tidak valid

    # Verifikasi password
    if not check_password_hash(user["password"], password):
        return (
            jsonify({"msg": "Kredensial tidak valid"}),
            401,
        )  # Ganti dengan 401 untuk kredensial yang tidak valid

    # Membuat access token
    access_token = create_access_token(identity=str(user["_id"]))
    refresh_token = create_refresh_token(
        identity=str(user["_id"])
    )  # Tambahkan refresh_token jika diperlukan

    # Kembalikan data dalam response
    return (
        jsonify(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,  # Kembalikan refresh_token
                "id": user["_id"],
                "email": user["email"],
            }
        ),
        200,
    )


@jwt_required()  # Memastikan token sudah terverifikasi
def profile():
    current_user_id = (
        get_jwt_identity()
    )  # Mendapatkan identity pengguna setelah token diverifikasi
    user = mongo.db.users.find_one({"_id": ObjectId(current_user_id)})

    if not user:
        return jsonify({"message": "Pengguna tidak ditemukan"}), 400

    return jsonify({"username": user["username"], "email": user["email"]}), 200


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
