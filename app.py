import os
from flask import Flask, render_template
from flask_jwt_extended import JWTManager, jwt_required
from flask_pymongo import PyMongo
from dotenv import load_dotenv
from flasgger import Swagger

load_dotenv()


def create_app():
    app = Flask(__name__)
    # Mengonfigurasi MongoDB dan JWT
    app.config["MONGO_URI"] = os.getenv(
        "MONGO_URI"
    )  # Pastikan MONGO_URI ada di file .env
    app.config["JWT_SECRET_KEY"] = os.getenv(
        "JWT_SECRET_KEY"
    )  # Pastikan JWT_SECRET_KEY ada di file .env

    mongo = PyMongo(app)
    jwt = JWTManager(app)
    swagger = Swagger(app, template_file="api_docs.yml")

    from controllers.api import init_api_routes, auth_controller
    from controllers.cms import cms_blueprints

    # Initialize API routes and get blueprints
    api_blueprints = init_api_routes(app, mongo)

    # Register semua blueprint (API dan Admin) secara otomatis
    for blueprint in api_blueprints + cms_blueprints:
        app.register_blueprint(blueprint)

    @app.route("/", methods=["GET"])
    def home():
        return render_template("index.html")

    @app.route("/api/auth/register/", methods=["POST"])
    def register():
        return auth_controller.register(mongo)

    @app.route("/api/auth/login/", methods=["POST"])
    def login():
        return auth_controller.login(mongo)

    @app.route("/api/auth/profile/", methods=["GET"])
    @jwt_required()
    def profile():
        return auth_controller.profile(mongo)

    return app, mongo, jwt


app, mongo, jwt = create_app()

if __name__ == "__main__":
    try:
        app.run(debug=True, host='0.0.0.0', port=5001)
    except Exception as e:
        print(f"Error: {e}")
