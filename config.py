import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "supersecretkey"
    JWT_SECRET = os.environ.get("JWT_SECRET") or "jwtsecretkey"
    API_KEY = os.environ.get("API_KEY") or "myapikey123"
