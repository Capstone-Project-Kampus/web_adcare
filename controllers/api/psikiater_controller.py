from flask import Blueprint, jsonify

api_psikiater = Blueprint("api_psikiater", __name__, url_prefix="/api/psikiater")

@api_psikiater.route("/all-psikiater", methods=["GET"])
def get_psikiaters():
    return jsonify({
        "message": "Get psikiaters"
    })
