from flask import Blueprint, jsonify

admin_articles = Blueprint("admin_articles", __name__, url_prefix="/admin/articles")

@admin_articles.route("/all-article", methods=["GET"])
def get_articles():
  return "Get articles"
