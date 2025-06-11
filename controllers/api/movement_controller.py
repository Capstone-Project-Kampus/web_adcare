from flask import Blueprint, request, jsonify
from datetime import datetime

from flask_jwt_extended import jwt_required

from controllers.api.middleware import api_key_required

movement_bp = Blueprint("movement_bp", __name__)

def init_movement_routes(mongo):
    @movement_bp.route("/api/movement", methods=["POST"])
    @jwt_required()
    @api_key_required
    def save_movement():
        try:
            data = request.get_json()
            required = ["head_move", "hand_move", "shoulder_move", "movement_score"]

            if not all(key in data for key in required):
                return jsonify({"error": "Missing fields"}), 400

            mongo.db.movements.insert_one({
                "head_move": data["head_move"],
                "hand_move": data["hand_move"],
                "shoulder_move": data["shoulder_move"],
                "movement_score": data["movement_score"],
                "timestamp": datetime.utcnow()
            })

            return jsonify({"message": "Movement saved successfully"}), 201

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return movement_bp
