# config.py
import os

class Config:
    # Secret key for sessions & CSRF
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-me")

    # Database URL (uses env var if set, falls back to local SQLite file)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///cougarhub.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
