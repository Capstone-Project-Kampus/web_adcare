import os
import uuid
from flask import Flask, render_template, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required
from itsdangerous import URLSafeTimedSerializer
from flask_pymongo import PyMongo
from dotenv import load_dotenv
from flasgger import Swagger
from werkzeug.utils import secure_filename
from functools import wraps
from flask_cors import CORS
from flask_mail import Mail

load_dotenv()


def create_app():
    app = Flask(__name__)
    # Mengonfigurasi MongoDB dan JWT
    app.config["MONGO_URI"] = os.getenv("MONGO_URI")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

    # API Key authentication
    app.config["API_KEY"] = os.getenv("API_KEY")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    def api_key_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            key = request.headers.get("x-api-key")
            if not key or key != app.config["API_KEY"]:
                return jsonify({"error": "Invalid or missing API key"}), 401
            return f(*args, **kwargs)

        return decorated

    # Configure upload settings
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static", "uploads")
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max file size
    app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif", "webp"}

    # Configure Mail
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USE_SSL"] = False
    app.config["MAIL_USERNAME"] = "f415alarr@gmail.com"
    app.config["MAIL_PASSWORD"] = "grxx nhdt yxsd nama"
    app.config["MAIL_DEFAULT_SENDER"] = ("AdCare", "f415alarr@gmail.com")

    s = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    mail = Mail(app)

    # Create uploads directory if it doesn't exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    mongo = PyMongo(app)
    jwt = JWTManager(app)
    swagger = Swagger(app, template_file="api_docs.yml")

    # CORS
    CORS(app, resources={r"/*": {"origins": "*"}})

    from controllers.api import init_api_routes, auth_controller
    from controllers.cms import cms_blueprints

    # Initialize API routes and get blueprints
    api_blueprints = init_api_routes(app, mongo, s, mail)

    # Register semua blueprint (API dan Admin) secara otomatis
    for blueprint in api_blueprints + cms_blueprints:
        app.register_blueprint(blueprint)

    def allowed_file(filename):
        """Check if file extension is allowed."""
        return (
            "." in filename
            and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
        )

    @app.route("/", methods=["GET"])
    @api_key_required
    def home():
        return render_template("index.html")

    @app.route("/api/auth/register/", methods=["POST"])
    @api_key_required
    def register():
        return auth_controller.register(mongo, s, mail)

    @app.route("/api/auth/login/", methods=["POST"])
    @api_key_required
    def login():
        return auth_controller.login(mongo)

    @app.route("/api/auth/profile/", methods=["GET"])
    @jwt_required()
    @api_key_required
    def profile():
        return auth_controller.profile(mongo)

    @app.route("/api/auth/confirm_email/<token>", methods=["GET"])
    @api_key_required
    def confirm_email(token):
        return auth_controller.confirm_email_acc(token, s)

    @app.route("/forgot_password/", methods=["POST"])
    @api_key_required
    def forgot_password():
        return auth_controller.forgot_pwd(s, mail)

    @app.route("/reset_password/<token>/", methods=["GET", "POST"])
    @api_key_required
    def reset_password(token):
        return auth_controller.reset_pwd(token, s)

    return app, mongo, jwt


app, mongo, jwt = create_app()

if __name__ == "__main__":
    try:
        app.run(debug=True, host="0.0.0.0", port=5001)
    except Exception as e:
        print(f"Error: {e}")
