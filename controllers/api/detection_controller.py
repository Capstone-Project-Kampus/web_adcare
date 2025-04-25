from flask import Blueprint, jsonify

api_detection = Blueprint("api_detection", __name__, url_prefix="/api/detection")

@api_detection.route("/all-detection", methods=["GET"])
def get_detections():
    return jsonify({
        "message": "Get detections"
    })
