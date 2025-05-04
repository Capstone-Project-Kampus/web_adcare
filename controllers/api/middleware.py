from flask import request, jsonify, current_app
from functools import wraps

def api_key_required(f):
    """Middleware to protect API routes with API key authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("x-api-key")
        if not key or key != current_app.config["API_KEY"]:
            return jsonify({"status": "error", "message": "Invalid or missing API key", "code": 401}), 401
        return f(*args, **kwargs)
    return decorated
