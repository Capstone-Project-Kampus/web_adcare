import os
from bson import ObjectId
from flask import *
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from flask_pymongo import PyMongo
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from .middleware import api_key_required
from flask_mail import *

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
            jsonify(
                {"status": "error", "message": "User tidak ditemukan", "code": 404}
            ),
            404,
        )
    if not user.get("is_verified"):
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Pengguna belum konfirmasi email",
                    "code": 404,
                }
            ),
            401,
        )
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


def register(mongo, s, mail):
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

    token = s.dumps(email, salt="email-confirm")
    confirm_url = url_for("confirm_email", token=token, _external=True)
    # HTML email template
    html = render_template_string(
        """
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: auto; padding: 20px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
            <!-- Logo Section -->
            <div style="text-align: center; padding-bottom: 10px;">
                <img src="https://sitesku.web.id/static/landing/img/logolongadcare.png" alt="AdCare Logo" style="width: 160px; height: 80px;">
            </div>
            
            <!-- Header Section -->
            <div style="background-color: #FF7C52; padding: 10px 20px; border-radius: 8px 8px 0 0; color: #ffffff; text-align: center;">
                <h2 style="margin: 0;">Welcome to AdCare!</h2>
            </div>
            
            <!-- Body Content -->
            <div style="padding: 20px;">
                <p>Hi {{ name }},</p>
                <p>Thank you for registering with AdCare. Please confirm your email address by clicking the button below:</p>
                <p style="text-align: center;">
                    <a href="{{ confirm_url }}" style="background-color: #FF7C52; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Confirm Email</a>
                </p>
                <p>If the button above doesn't work, copy and paste the following link into your browser:</p>
                <p style="word-break: break-all; color: #555;"><a href="{{ confirm_url }}">{{ confirm_url }}</a></p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="font-size: 12px; color: #777;">If you did not register for an AdCare account, please ignore this email.</p>
            </div>
        </div>
    </body>
    </html>
    """,
        name=username,
        confirm_url=confirm_url,
    )

    msg = Message(
        "Confirm Your Email", sender="AdCare <f415alarr@gmail.com>", recipients=[email]
    )
    msg.html = html
    mail.send(msg)

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


def confirm_email_acc(token, s):
    try:
        email = s.loads(token, salt="email-confirm", max_age=3600)
    except:
        html = render_template_string(
            """
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body style="font-family: Arial, sans-serif; color: #333; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: auto; padding: 20px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
                <div style="text-align: center; padding-bottom: 10px;">
                    <img src="https://sitesku.web.id/static/landing/img/logolongadcare.png" alt="AdCare Logo" style="width: 80px; height: auto;">
                </div>
                <div style="background-color: #FF7C52; padding: 10px 20px; border-radius: 8px 8px 0 0; color: #ffffff; text-align: center;">
                    <h2 style="margin: 0; font-size: 1.5rem;">Invalid Link</h2>
                </div>
                <div style="padding: 20px;">
                    <p style="font-size: 1rem;">The confirmation link is either invalid or has expired. Please request a new confirmation link.</p>
                </div>
            </div>
        </body>
        </html>
        """
        )
        return html, 400

    user = mongo.db.users.find_one({"email": email})
    if user.get("is_verified"):
        html = render_template_string(
            """
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body style="font-family: Arial, sans-serif; color: #333; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: auto; padding: 20px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
                <div style="text-align: center; padding-bottom: 10px;">
                    <img src="https://sitesku.web.id/static/landing/img/logolongadcare.png" alt="AdCare Logo" style="width: 80px; height: auto;">
                </div>
                <div style="background-color: #ffc107; padding: 10px 20px; border-radius: 8px 8px 0 0; color: #ffffff; text-align: center;">
                    <h2 style="margin: 0; font-size: 1.5rem;">Already Verified</h2>
                </div>
                <div style="padding: 20px;">
                    <p style="font-size: 1rem;">Your email address has already been confirmed. You can now log in.</p>
                </div>
            </div>
        </body>
        </html>
        """
        )
        return html, 400
    else:
        mongo.db.users.update_one({"email": email}, {"$set": {"is_verified": True}})
        html = render_template_string(
            """
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body style="font-family: Arial, sans-serif; color: #333; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: auto; padding: 20px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
                <div style="text-align: center; padding-bottom: 10px;">
                    <img src="https://sitesku.web.id/static/landing/img/logolongadcare.png" alt="AdCare Logo" style="width: 80px; height: auto;">
                </div>
                <div style="background-color: #FF7C52; padding: 10px 20px; border-radius: 8px 8px 0 0; color: #ffffff; text-align: center;">
                    <h2 style="margin: 0; font-size: 1.5rem;">Email Confirmed</h2>
                </div>
                <div style="padding: 20px;">
                    <p style="font-size: 1rem;">Your email address has been successfully verified. You can now log in to AdCare Apps.</p>
                </div>
            </div>
        </body>
        </html>
        """
        )
        return html, 200


def forgot_pwd(s, mail):
    data = request.get_json()
    email = data.get("email")
    user = Users.query.filter_by(email=email).first()

    if not user:
        return jsonify({"message": "Email tidak ditemukan."}), 404

    token = s.dumps(email, salt="reset-password")
    reset_url = url_for("reset_password", token=token, _external=True)

    # HTML template for the email
    html = render_template_string(
        """
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: auto; padding: 20px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
            <!-- Logo Section -->
            <div style="text-align: center; padding-bottom: 10px;">
                <img src="https://agrolyn.my.id/static/assets/favicon.png" alt="Agrolyn Logo" style="width: 80px; height: 80px;">
            </div>

            <!-- Header Section -->
            <div style="background-color: #4CAF50; padding: 10px 20px; border-radius: 8px 8px 0 0; color: #ffffff; text-align: center;">
                <h2 style="margin: 0;">Reset Your Password</h2>
            </div>
            
            <!-- Body Content -->
            <div style="padding: 20px;">
                <p>Hello,</p>
                <p>You requested a password reset for your account. Please click the button below to set a new password:</p>
                <p style="text-align: center;">
                    <a href="{{ reset_url }}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a>
                </p>
                <p>If the button above doesn't work, copy and paste the following link into your browser:</p>
                <p style="word-break: break-all; color: #555;"><a href="{{ reset_url }}">{{ reset_url }}</a></p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="font-size: 12px; color: #777;">If you did not request this, please ignore this email.</p>
            </div>
        </div>
    </body>
    </html>
    """,
        reset_url=reset_url,
    )

    msg = Message(
        "Password Reset Request",
        sender="AGROLYN <kareltrisnanto26@gmail.com>",
        recipients=[email],
    )
    msg.html = html
    mail.send(msg)

    return (
        jsonify({"message": "Email pengaturan ulang kata sandi telah terkirim."}),
        200,
    )


def reset_pwd(token, s):
    if request.method == "GET":
        return render_template("reset_password.html", token=token)

    elif request.method == "POST":
        try:
            # Verifikasi token
            email = s.loads(token, salt="reset-password", max_age=3600)
        except Exception as e:
            return render_template(
                "reset_password.html", token=token, error="Link is invalid or expired."
            )

        new_password = request.json.get(
            "new_password"
        )  # Mengambil password baru dari JSON
        user = Users.query.filter_by(email=email).first()

        if not user:
            return render_template(
                "reset_password.html", token=token, error="User not found."
            )

        # Update password
        user.set_password(new_password)
        db.session.commit()

        return render_template("reset_password_success.html")


def login_with_google():
    data = request.get_json()

    if "token_id" not in data or data["token_id"] == "":
        return jsonify(
            {
                "code": 400,
                "status": "bad request",
                "message": f"field token_id can't be empty",
            }
        )

    token_id = data["token_id"]

    try:
        idInfo = id_token.verify_oauth2_token(
            token_id, GoogleRequest(), os.getenv("GOOGLE_CLIENT_ID")
        )
    except Exception as e:
        print(e)
        return (
            jsonify(
                {"code": 400, "status": "bad request", "message": f"Invalid token_id"}
            ),
            400,
        )

    email = idInfo.get("email")
    name = idInfo.get("username")

    user = mongo.db.users.find_one({"email": email})

    if not user:
        user = mongo.db.users.insert_one({"email": email, "username": name}).inserted_id

    access_token = create_access_token(identity=str(user))
    refresh_token = create_refresh_token(identity=str(user))

    return (
        jsonify(
            {
                "code": 200,
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


def init_auth_routes(app, mongo_instance, s, mail):
    global mongo
    mongo = mongo_instance

    api_auth = Blueprint("api_auth", __name__, url_prefix="/api/auth")

    @api_auth.route("/register", methods=["POST"])
    def blueprint_register():
        return register(mongo, s, mail)

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
