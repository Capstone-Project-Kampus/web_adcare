from flask import Blueprint, jsonify

api_articles = Blueprint("api_articles", __name__, url_prefix="/api/articles")

@api_articles.route("/all-article", methods=["GET"])
def get_articles():
    return jsonify({
        "message": "Get articles"
    })
