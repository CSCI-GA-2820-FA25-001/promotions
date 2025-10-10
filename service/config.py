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
    "mysql+pymysql://appuser:appuserpass@mysql:3306/mydb"
)

SQLALCHEMY_DATABASE_URI = DATABASE_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False
# SQLALCHEMY_POOL_SIZE = 2  # optional

# ---------------------------------------------------------------------
# Security & Logging
# ---------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "sup3r-s3cr3t")
LOGGING_LEVEL = logging.INFO
