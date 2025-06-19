from flask import Blueprint, request, jsonify
from datetime import datetime
from flask_jwt_extended import get_jwt_identity, jwt_required
from controllers.api.middleware import api_key_required

movement_bp = Blueprint("movement_bp", _name_)


def init_movement_routes(mongo):
    @movement_bp.route("/api/movement", methods=["POST"])
    @jwt_required()
    @api_key_required
    def save_movement():
        try:
            data = request.get_json()
            userId = get_jwt_identity()
            required = [
                "head_move",
                "hand_move",
                "shoulder_move",
                "movement_score",
                "result",
            ]

            if not all(key in data for key in required):
                return jsonify({"error": "Missing fields"}), 400

            mongo.db.movements.insert_one(
                {
                    "head_move": data["head_move"],
                    "hand_move": data["hand_move"],
                    "shoulder_move": data["shoulder_move"],
                    "movement_score": data["movement_score"],
                    "result": str(data["result"]),
                    "user_id": userId,
                    "timestamp": datetime.utcnow(),
                }
            )

            return jsonify({"message": "Movement saved successfully"}), 201

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @movement_bp.route("/api/movement/history", methods=["GET"])
    @jwt_required()
    @api_key_required
    def history_movement():
        try:
            userId = get_jwt_identity()

            history_cursor = mongo.db.movements.find({"user_id": userId}).sort(
                "timestamp", -1
            )

            history = []
            for doc in history_cursor:
                doc["_id"] = str(doc["_id"])
                doc["timestamp"] = doc["timestamp"].isoformat()
                history.append(doc)

            return jsonify({"history": history}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return movement_bp
