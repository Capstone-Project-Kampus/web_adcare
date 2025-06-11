# import os
# import json
# import requests
# from flask import Blueprint, jsonify, request, current_app, url_for, redirect
# from flask_pymongo import PyMongo
# from flask_jwt_extended import create_access_token, create_refresh_token
# from werkzeug.security import generate_password_hash
# from datetime import timedelta
# from google.oauth2 import id_token
# from google.auth.transport import requests as google_requests

# # Global variable untuk instance MongoDB
# mongo = None

# # Client ID dari file google-services.json
# GOOGLE_CLIENT_ID = "525552816742-nmifresd3ekue0ufft3957210kc4ks4v.apps.googleusercontent.com"

# def set_mongo(mongo_instance):
#     global mongo
#     mongo = mongo_instance

# def verify_google_token(token):
#     """Verifikasi token ID Google dan mengembalikan informasi pengguna"""
#     try:
#         # Verify the token
#         idinfo = id_token.verify_oauth2_token(
#             token, google_requests.Request(), GOOGLE_CLIENT_ID
#         )

#         # ID token is valid
#         return {
#             "status": "success",
#             "user_info": {
#                 "google_id": idinfo.get("sub"),
#                 "email": idinfo.get("email"),
#                 "name": idinfo.get("name"),
#                 "picture": idinfo.get("picture")
#             }
#         }
#     except ValueError as e:
#         # Invalid token
#         return {"status": "error", "message": str(e)}

# def google_auth():
#     """Endpoint untuk autentikasi dengan Google dari aplikasi mobile"""
#     global mongo
#     if mongo is None:
#         return jsonify({"status": "error", "message": "Database tidak terhubung", "code": 500}), 500

#     # Dapatkan token dari request
#     token = request.json.get("id_token")
#     if not token:
#         return jsonify({"status": "error", "message": "Token ID tidak ditemukan", "code": 400}), 400

#     # Verifikasi token Google
#     result = verify_google_token(token)
#     if result["status"] == "error":
#         return jsonify({"status": "error", "message": result["message"], "code": 401}), 401

#     # Dapatkan informasi pengguna
#     user_info = result["user_info"]
#     google_id = user_info["google_id"]
#     email = user_info["email"]
#     name = user_info["name"]
#     picture = user_info["picture"]

#     # Cek apakah pengguna sudah ada di database
#     user = mongo.db.users.find_one({"google_id": google_id})

#     # Jika tidak ada, buat pengguna baru
#     if not user:
#         # Cek apakah email sudah digunakan (mungkin dengan metode login lain)
#         existing_user = mongo.db.users.find_one({"email": email})
#         if existing_user:
#             # Jika email sudah ada, tambahkan google_id ke user yang sudah ada
#             mongo.db.users.update_one(
#                 {"_id": existing_user["_id"]},
#                 {"$set": {"google_id": google_id, "profile_picture": picture}}
#             )
#             user = mongo.db.users.find_one({"_id": existing_user["_id"]})
#         else:
#             # Buat user baru
#             new_user = {
#                 "email": email,
#                 "username": name,
#                 "google_id": google_id,
#                 "profile_picture": picture,
#                 "password": generate_password_hash("google-oauth-" + google_id),  # Password dummy aman
#                 "auth_type": "google"
#             }
#             result = mongo.db.users.insert_one(new_user)
#             user = mongo.db.users.find_one({"_id": result.inserted_id})

#     # Buat token JWT
#     access_token = create_access_token(
#         identity=str(user["_id"]),
#         expires_delta=timedelta(days=2)
#     )
#     refresh_token = create_refresh_token(identity=str(user["_id"]))

#     # Kembalikan data user dan token
#     return jsonify({
#         "status": "success",
#         "message": "Login berhasil dengan Google",
#         "data": {
#             "access_token": access_token,
#             "refresh_token": refresh_token,
#             "user": {
#                 "id": str(user["_id"]),
#                 "email": user["email"],
#                 "username": user["username"],
#                 "profile_picture": user.get("profile_picture", "")
#             },
#             "api_key": os.getenv("API_KEY"),
#         },
#         "code": 200
#     }), 200

# def init_google_auth_routes(app, mongo_instance):
#     """
#     Inisialisasi route untuk Google OAuth
#     """
#     set_mongo(mongo_instance)

#     google_auth_bp = Blueprint('google_auth', __name__)

#     # Route untuk autentikasi Google (dipanggil dari aplikasi mobile)
#     @google_auth_bp.route('/api/auth/google', methods=['POST'])
#     def google_auth_endpoint():
#         return google_auth()

#     return google_auth_bp
