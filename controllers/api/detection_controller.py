from flask import Blueprint, jsonify
from .middleware import api_key_required

api_detection = Blueprint("api_detection", __name__, url_prefix="/api/detection")

@api_detection.route("/all-detection", methods=["GET"])
@api_key_required
def get_detections():
    return jsonify({
        "message": "Get detections"
    })
