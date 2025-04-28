import os
from flask import Flask, render_template
from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo
from controllers.api import api_blueprints, auth_controller
from controllers.cms import cms_blueprints
from dotenv import load_dotenv
from flasgger import Swagger

load_dotenv()

app = Flask(__name__)
# Mengonfigurasi MongoDB dan JWT
app.config['MONGO_URI'] = os.getenv("MONGO_URI")  # Pastikan MONGO_URI ada di file .env
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")  # Pastikan JWT_SECRET_KEY ada di file .env


mongo = PyMongo(app)
jwt = JWTManager(app)

swagger = Swagger(app, template_file='api_docs.yml')


# Register semua blueprint (API dan Admin) secara otomatis
for bp in api_blueprints + cms_blueprints:
    app.register_blueprint(bp)

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/register/", methods=["POST"])
def register():
    return auth_controller.register()

@app.route("/login/", methods=["POST"])
def login():
    return auth_controller.login()

@app.route("/profile/", methods=["GET"])
def profile():
    return auth_controller.profile()

if __name__ == "__main__":
    app.run(debug=True)
