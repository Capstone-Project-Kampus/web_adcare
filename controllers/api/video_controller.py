from flask import Blueprint, jsonify

api_video = Blueprint("api_video", __name__, url_prefix="/api/videos")

@api_video.route("/all-video", methods=["GET"])
def get_videos():
    return jsonify({
        "message": "Get videos"
    })
