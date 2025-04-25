from flask import Blueprint, jsonify

admin_detection = Blueprint("admin_detection", __name__, url_prefix="/admin/detection")

@admin_detection.route("/all-detection", methods=["GET"])
def get_detections():
    return "Get detections"
