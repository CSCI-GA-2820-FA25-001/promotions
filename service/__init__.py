# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Package: service
Package for the application models and service routes
This module creates and configures the Flask app and sets up the logging
and SQL database
"""
import sys
from flask import Flask
from flask_migrate import Migrate
from service import config
from service.models import db
from service.common import log_handlers

############################################################
# Initialize the Flask instance
############################################################


def create_app():
    """Initialize the core application."""
    flask_app = Flask(__name__)
    flask_app.config.from_object(config)

    # Initialize SQLAlchemy & Migrations
    db.init_app(flask_app)
    Migrate(flask_app, db)

    with flask_app.app_context():
        from service import models  # noqa: F401
        from service.common import error_handlers, cli_commands  # noqa: F401

        # Import and register routes
        from service import routes

        routes.init_routes(flask_app)

        # Ensure database tables are created for local dev & pytest
        try:
            db.create_all()
            flask_app.logger.info("Database tables created successfully.")
        except Exception as error:  # pylint: disable=broad-except
            flask_app.logger.warning(f"Database initialization skipped: {error}")

        # Configure logging
        log_handlers.init_logging(flask_app, "gunicorn.error")

        # Register error handlers
        error_handlers.register_handlers(flask_app)

        flask_app.logger.info(70 * "*")
        flask_app.logger.info("  S E R V I C E   R U N N I N G  ".center(70, "*"))
        flask_app.logger.info(70 * "*")
        flask_app.logger.info("Service initialized!")

    # Register CLI commands safely
    try:
        if hasattr(cli_commands, "db_create"):
            flask_app.cli.add_command(cli_commands.db_create)
        if hasattr(cli_commands, "db_drop"):
            flask_app.cli.add_command(cli_commands.db_drop)
    except Exception as e:
        flask_app.logger.warning(f"CLI commands not registered: {e}")

    return flask_app


# Flask CLI instance
app = create_app()
