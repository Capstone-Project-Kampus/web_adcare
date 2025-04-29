from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename
import os
import uuid


def init_psikiater_controller_routes(app, mongo):
    api_psikiater = Blueprint("api_psikiater", __name__, url_prefix="/api/psikiater")

    def allowed_file(filename):
        """Check if file extension is allowed."""
        ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
        return (
            "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
        )

    @api_psikiater.route("/all-psikiater", methods=["GET"])
    @jwt_required()
    def get_psikiaters():
        # Use the mongo instance passed from app initialization
        psikiaters = list(mongo.db.psikiaters.find())

        if not psikiaters:
            return jsonify({"message": "No psikiaters found"}), 404

        # Convert ObjectId to string for JSON serialization
        for psikiater in psikiaters:
            psikiater["_id"] = str(psikiater["_id"])

        return jsonify({"message": "Get psikiaters", "data": psikiaters})

    @api_psikiater.route("/create", methods=["POST"])
    @jwt_required()
    def create_psikiater():
        # Check if the request contains form data
        if "nama" not in request.form:
            return jsonify({"error": "Missing required field: nama"}), 400

        # Validate required fields
        required_fields = ["nama", "biografi", "pendidikan", "dinas", "nomor_hp"]
        for field in required_fields:
            if field not in request.form:
                return jsonify({"error": f"{field} is required"}), 400

        # Handle file upload
        foto_url = ""
        if "foto" in request.files:
            foto = request.files["foto"]
            if foto and allowed_file(foto.filename):
                # Generate a unique filename
                ext = foto.filename.rsplit(".", 1)[1].lower()
                filename = f"{uuid.uuid4()}.{ext}"
                filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

                # Save the file
                foto.save(filepath)
                foto_url = f"/static/uploads/{filename}"
            elif foto:
                return jsonify({"error": "File type not allowed"}), 400

        new_psikiater = {
            "nama": request.form["nama"],
            "foto": foto_url,
            "biografi": request.form["biografi"],
            "pendidikan": request.form["pendidikan"],
            "dinas": request.form["dinas"],
            "nomor_hp": request.form["nomor_hp"],
        }

        try:
            result = mongo.db.psikiaters.insert_one(new_psikiater)
            return (
                jsonify(
                    {
                        "message": "Psikiater created successfully",
                        "data": {
                            "id": str(result.inserted_id),
                            "nama": new_psikiater["nama"],
                            "foto": new_psikiater["foto"],
                        },
                    }
                ),
                201,
            )
        except Exception as e:
            # If file was uploaded but insertion failed, remove the file
            if foto_url and os.path.exists(
                os.path.join(
                    current_app.config["UPLOAD_FOLDER"], foto_url.split("/")[-1]
                )
            ):
                os.remove(
                    os.path.join(
                        current_app.config["UPLOAD_FOLDER"], foto_url.split("/")[-1]
                    )
                )
            return jsonify({"error": str(e)}), 500

    @api_psikiater.route("/update/<psikiater_id>", methods=["PUT"])
    @jwt_required()
    def update_psikiater(psikiater_id):
        from bson import ObjectId

        # Prepare update fields
        update_fields = {}
        foto_url = None

        # First, check if the psikiater exists
        try:
            existing_psikiater = mongo.db.psikiaters.find_one(
                {"_id": ObjectId(psikiater_id)}
            )

            # If psikiater not found, return 404
            if not existing_psikiater:
                return jsonify({"error": "Psikiater not found"}), 404

        except Exception as e:
            return jsonify({"error": f"Invalid psikiater ID: {str(e)}"}), 400

        # Handle file upload if present
        if "foto" in request.files:
            foto = request.files["foto"]
            if foto and allowed_file(foto.filename):
                # Generate a unique filename
                ext = foto.filename.rsplit(".", 1)[1].lower()
                filename = f"{uuid.uuid4()}.{ext}"
                filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

                # Save the file
                foto.save(filepath)
                foto_url = f"/static/uploads/{filename}"
                update_fields["foto"] = foto_url
            elif foto:
                return jsonify({"error": "File type not allowed"}), 400

        # Update other fields from form data
        fields_map = {
            "nama": "nama",
            "biografi": "biografi",
            "pendidikan": "pendidikan",
            "dinas": "dinas",
            "nomor_hp": "nomor_hp",
        }

        for form_key, db_key in fields_map.items():
            if form_key in request.form:
                update_fields[db_key] = request.form[form_key]

        # If no update fields provided, return error
        if not update_fields:
            return jsonify({"error": "No update fields provided"}), 400

        try:
            # If updating foto, delete the old foto file
            if foto_url and existing_psikiater.get("foto"):
                old_filename = existing_psikiater["foto"].split("/")[-1]
                old_filepath = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], old_filename
                )
                if os.path.exists(old_filepath):
                    os.remove(old_filepath)

            # Perform the update
            result = mongo.db.psikiaters.update_one(
                {"_id": ObjectId(psikiater_id)}, {"$set": update_fields}
            )

            if result.modified_count == 0:
                return (
                    jsonify({"message": "No changes made to psikiater"}),
                    200,
                )

            updated_psikiater = mongo.db.psikiaters.find_one(
                {"_id": ObjectId(psikiater_id)}
            )
            updated_psikiater["_id"] = str(updated_psikiater["_id"])

            return jsonify(
                {"message": "Psikiater updated successfully", "data": updated_psikiater}
            )
        except Exception as e:
            # Clean up newly uploaded file if update fails
            if foto_url:
                filepath = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], foto_url.split("/")[-1]
                )
                if os.path.exists(filepath):
                    os.remove(filepath)
            return jsonify({"error": str(e)}), 500

    @api_psikiater.route("/delete/<psikiater_id>", methods=["DELETE"])
    @jwt_required()
    def delete_psikiater(psikiater_id):
        from bson import ObjectId

        try:
            # First, find the psikiater to get the foto path
            psikiater = mongo.db.psikiaters.find_one({"_id": ObjectId(psikiater_id)})

            # Delete the associated foto file if it exists
            if psikiater and psikiater.get("foto"):
                foto_filename = psikiater["foto"].split("/")[-1]
                foto_filepath = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], foto_filename
                )
                if os.path.exists(foto_filepath):
                    os.remove(foto_filepath)

            # Delete the psikiater from the database
            result = mongo.db.psikiaters.delete_one({"_id": ObjectId(psikiater_id)})

            if result.deleted_count == 0:
                return jsonify({"message": "No psikiater found"}), 404

            return jsonify(
                {
                    "message": "Psikiater deleted successfully",
                    "data": {"id": psikiater_id},
                }
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return api_psikiater
