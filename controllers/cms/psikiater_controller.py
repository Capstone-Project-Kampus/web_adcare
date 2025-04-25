from flask import Blueprint, jsonify

admin_psikiater = Blueprint("admin_psikiater", __name__, url_prefix="/admin/psikiater")

@admin_psikiater.route("/all-psikiater", methods=["GET"])
def get_psikiaters():
    return "Get psikiaters"
