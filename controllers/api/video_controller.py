from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from bson import ObjectId


def init_video_controller_routes(app, mongo):
    api_video = Blueprint("api_video", __name__, url_prefix="/api/videos")

    @api_video.route("/all-video", methods=["GET"])
    @jwt_required()
    def get_videos():
        videos = list(mongo.db.videos.find())
        if len(videos) == 0:
            return jsonify({"message": "No videos found", "data": []}), 200

        # Convert ObjectId to string for JSON serialization
        video_list = []
        for video in videos:
            video_dict = {
                "_id": str(video["_id"]),
                "title": video.get("title", ""),
                "url": video.get("url", ""),
                "description": video.get("description", "")
            }
            video_list.append(video_dict)

        return jsonify({
            "message": "Videos retrieved successfully",
            "data": video_list
        }), 200

    @api_video.route("/create", methods=["POST"])
    @jwt_required()
    def create_video():
        data = request.get_json()

        # Validate required fields
        required_fields = ["title", "url"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400

        # Create video document
        video_data = {
            "_id": ObjectId(),
            "title": data["title"],
            "url": data["url"],
            "description": data.get("description", "")
        }

        try:
            mongo.db.videos.insert_one(video_data)
            return jsonify({
                "message": "Video created successfully",
                "data": {
                    "_id": str(video_data["_id"]),
                    "title": video_data["title"],
                    "url": video_data["url"]
                }
            }), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api_video.route("/update/<video_id>", methods=["PUT"])
    @jwt_required()
    def update_video(video_id):
        try:
            # Validate video_id
            video = mongo.db.videos.find_one({"_id": ObjectId(video_id)})
            if not video:
                return jsonify({"error": "Video not found"}), 404

            # Get update data
            data = request.get_json()

            # Prepare update fields
            update_fields = {}
            if "title" in data:
                update_fields["title"] = data["title"]
            if "url" in data:
                update_fields["url"] = data["url"]
            if "description" in data:
                update_fields["description"] = data["description"]

            # Perform update
            mongo.db.videos.update_one(
                {"_id": ObjectId(video_id)},
                {"$set": update_fields}
            )

            # Fetch updated video
            updated_video = mongo.db.videos.find_one({"_id": ObjectId(video_id)})
            return jsonify({
                "message": "Video updated successfully",
                "data": {
                    "_id": str(updated_video["_id"]),
                    "title": updated_video.get("title", ""),
                    "url": updated_video.get("url", "")
                }
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api_video.route("/delete/<video_id>", methods=["DELETE"])
    @jwt_required()
    def delete_video(video_id):
        try:
            # Validate video_id and delete
            result = mongo.db.videos.delete_one({"_id": ObjectId(video_id)})
            
            if result.deleted_count == 0:
                return jsonify({"error": "Video not found"}), 404

            return jsonify({
                "message": "Video deleted successfully", 
                "data": {"_id": video_id}
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return api_video
