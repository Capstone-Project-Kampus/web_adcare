from flask import Blueprint, jsonify

admin_video = Blueprint("admin_video", __name__, url_prefix="/admin/videos")

@admin_video.route("/all-video", methods=["GET"])
def get_videos():
    return "Get videos"
