"""
Global Configuration for Application
"""
import os
import logging

# ---------------------------------------------------------------------
# Database Configuration
# ---------------------------------------------------------------------
DATABASE_URI = os.getenv(
    "DATABASE_URI",
    "postgresql+psycopg://postgres:postgres@postgres:5432/mydb"
)

SQLALCHEMY_DATABASE_URI = DATABASE_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False

# ---------------------------------------------------------------------
# Security & Logging
# ---------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "sup3r-s3cr3t")
LOGGING_LEVEL = logging.INFO
