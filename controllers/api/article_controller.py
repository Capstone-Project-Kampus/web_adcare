from flask import Blueprint, jsonify, request
from bson import ObjectId
from flask_jwt_extended import jwt_required, get_jwt_identity
from pymongo import DESCENDING
from datetime import datetime
from flask import current_app

api_articles = Blueprint("api_articles", __name__, url_prefix="/api/articles")

@api_articles.route("/all-article", methods=["GET"])
def get_articles():
    try:
        # Pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Fetch articles from MongoDB
        mongo = current_app.config['MONGO']
        total_articles = mongo.db.articles.count_documents({})
        
        # Calculate pagination details
        total_pages = (total_articles + per_page - 1) // per_page
        
        # Fetch paginated articles
        articles = list(mongo.db.articles.find()
                        .sort('created_at', DESCENDING)
                        .skip((page - 1) * per_page)
                        .limit(per_page))
        
        # Convert ObjectId to string
        for article in articles:
            article['_id'] = str(article['_id'])
        
        return jsonify({
            "status": "success",
            "message": "Articles retrieved successfully",
            "data": {
                "articles": articles,
                "pagination": {
                    "total_articles": total_articles,
                    "total_pages": total_pages,
                    "current_page": page,
                    "per_page": per_page
                }
            },
            "code": 200
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error retrieving articles: {str(e)}",
            "code": 500
        }), 500

@api_articles.route("/create", methods=["POST"])
@jwt_required()
def create_article():
    try:
        # Get current user ID
        current_user_id = get_jwt_identity()
        
        # Get article data from request
        data = request.json
        
        # Input validation
        if not data or not data.get('title') or not data.get('content'):
            return jsonify({
                "status": "error",
                "message": "Title and content are required",
                "code": 400
            }), 400
        
        mongo = current_app.config['MONGO']
        
        # Create article document
        new_article = {
            "title": data['title'],
            "content": data['content'],
            "author_id": ObjectId(current_user_id),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Optional fields
        if data.get('tags'):
            new_article['tags'] = data['tags']
        
        result = mongo.db.articles.insert_one(new_article)
        
        return jsonify({
            "status": "success",
            "message": "Article created successfully",
            "data": {
                "article_id": str(result.inserted_id),
                "title": new_article['title']
            },
            "code": 201
        }), 201
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error creating article: {str(e)}",
            "code": 500
        }), 500

@api_articles.route("/<article_id>", methods=["GET"])
def get_article(article_id):
    try:
        mongo = current_app.config['MONGO']
        
        # Validate ObjectId
        try:
            article_object_id = ObjectId(article_id)
        except:
            return jsonify({
                "status": "error",
                "message": "Invalid article ID",
                "code": 400
            }), 400
        
        article = mongo.db.articles.find_one({"_id": article_object_id})
        
        if not article:
            return jsonify({
                "status": "error",
                "message": "Article not found",
                "code": 404
            }), 404
        
        # Convert ObjectId to string
        article['_id'] = str(article['_id'])
        article['author_id'] = str(article['author_id'])
        
        return jsonify({
            "status": "success",
            "message": "Article retrieved successfully",
            "data": article,
            "code": 200
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error retrieving article: {str(e)}",
            "code": 500
        }), 500
