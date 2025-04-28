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
    password = request.json.get('password')

    if not username or not password:
        return jsonify({'msg': 'Username dan password harus diisi'}), 400

    if mongo.db.users.find_one({'username': username}):
        return jsonify({'msg': 'Pengguna sudah ada'}), 400

    hashed_password = generate_password_hash(password)

    mongo.db.users.insert_one({
        'username': username,
        'password': hashed_password,
        'api_key': None
    })

    return jsonify({'msg': 'Registrasi berhasil'}), 201

def login():
    username = request.json.get('username')
    password = request.json.get('password')

    user = mongo.db.users.find_one({'username': username})
    if not user:
        return jsonify({'msg': 'Pengguna tidak ditemukan'}), 400

    # Cek password pakai check_password_hash
    if not check_password_hash(user['password'], password):
        return jsonify({'msg': 'Kredensial tidak valid'}), 400

    access_token = create_access_token(identity=str(user['_id']))
    return jsonify({'access_token': access_token}), 200


@jwt_required()  # Memastikan token sudah terverifikasi
def profile():
    current_user_id = get_jwt_identity()  # Mendapatkan identity pengguna setelah token diverifikasi
    user = mongo.db.users.find_one({'_id': ObjectId(current_user_id)})
    
    if not user:
        return jsonify({'msg': 'Pengguna tidak ditemukan'}), 400

    return jsonify({'username': user['username']}), 200