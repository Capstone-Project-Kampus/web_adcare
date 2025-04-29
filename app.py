import os
import uuid
from flask import Flask, render_template, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required
from flask_pymongo import PyMongo
from dotenv import load_dotenv
from flasgger import Swagger
from werkzeug.utils import secure_filename

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

    # Configure upload settings
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max file size
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Create uploads directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

    def allowed_file(filename):
        """Check if file extension is allowed."""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    @app.route("/", methods=["GET"])
    def home():
        return render_template("index.html")

    @app.route("/api/upload/image", methods=["POST"])
    @jwt_required()
    def upload_image():
        """
        Upload an image to the server.
        Returns the filename of the uploaded image.
        """
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        if file and allowed_file(file.filename):
            # Generate a unique filename
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4()}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save the file
            file.save(filepath)
            
            return jsonify({
                "message": "File uploaded successfully", 
                "filename": filename,
                "url": f"/static/uploads/{filename}"
            }), 201
        
        return jsonify({"error": "File type not allowed"}), 400

    @app.route("/api/delete/image/<filename>", methods=["DELETE"])
    @jwt_required()
    def delete_image(filename):
        """
        Delete an uploaded image from the server.
        """
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return jsonify({
                    "message": "File deleted successfully", 
                    "filename": filename
                }), 200
            else:
                return jsonify({"error": "File not found"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500

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
