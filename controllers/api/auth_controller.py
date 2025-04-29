from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, get_jwt_identity,jwt_required
from werkzeug.security import generate_password_hash, check_password_hash

from app import app

mongo = PyMongo(app)

api_auth = Blueprint("api_auth", __name__, url_prefix="/api/auth")

@jwt_required(refresh=True)  # Membutuhkan refresh token
def refresh_token():
    identity = get_jwt_identity()
    new_access_token = create_access_token(identity=identity)
    return jsonify({
        "message": "Refresh token"
    })

def register():
    username = request.json.get('username')
    email = request.json.get('email')
    password = request.json.get('password')

    # Memeriksa apakah username, email, atau password kosong
    if not username or not password or not email:
        return jsonify({'msg': 'Email, Username dan Password harus diisi'}), 400

    # Memeriksa apakah email sudah ada
    if mongo.db.users.find_one({'email': email}):
        return jsonify({'msg': 'Pengguna sudah ada'}), 400

    # Meng-hash password
    hashed_password = generate_password_hash(password)

    # Menyimpan pengguna baru ke database
    mongo.db.users.insert_one({
        'email': email,
        'username': username,
        'password': hashed_password,
        'api_key': None
    })

    return jsonify({'msg': 'Registrasi berhasil'}), 201


def login():
    email = request.json.get('email')
    password = request.json.get('password')

    # Mencari pengguna di database
    user = mongo.db.users.find_one({'email': email})
    if not user:
        return jsonify({'msg': 'Pengguna tidak ditemukan'}), 401  # Ganti dengan 401 untuk kredensial yang tidak valid

    # Verifikasi password
    if not check_password_hash(user['password'], password):
        return jsonify({'msg': 'Kredensial tidak valid'}), 401  # Ganti dengan 401 untuk kredensial yang tidak valid

    # Membuat access token
    access_token = create_access_token(identity=str(user['_id']))
    refresh_token = create_refresh_token(identity=str(user['_id']))  # Tambahkan refresh_token jika diperlukan

    # Kembalikan data dalam response
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,  # Kembalikan refresh_token
        'id': user['_id'],
        'email': user['email'],
    }), 200



@jwt_required()  # Memastikan token sudah terverifikasi
def profile():
    current_user_id = get_jwt_identity()  # Mendapatkan identity pengguna setelah token diverifikasi
    user = mongo.db.users.find_one({'_id': ObjectId(current_user_id)})
    
    if not user:
        return jsonify({'msg': 'Pengguna tidak ditemukan'}), 400

    return jsonify({'username': user['username'], 'email': user['email']}), 200