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
    app = Flask(__name__)
    app.config.from_object(config)

    # Initialize SQLAlchemy & Migrations
    db.init_app(app)
    Migrate(app, db)

    with app.app_context():
        from service import routes, models  # noqa: F401
        from service.common import error_handlers, cli_commands  # noqa: F401

        # Ensure database tables are created for local dev & pytest
        try:
            db.create_all()
            app.logger.info("Database tables created successfully.")
        except Exception as error:  # pylint: disable=broad-except
            app.logger.warning(f"Database initialization skipped: {error}")

        # Configure logging
        log_handlers.init_logging(app, "gunicorn.error")

        # Register error handlers if available
        if hasattr(error_handlers, "register_handlers"):
            error_handlers.register_handlers(app)

        app.logger.info(70 * "*")
        app.logger.info("  S E R V I C E   R U N N I N G  ".center(70, "*"))
        app.logger.info(70 * "*")
        app.logger.info("Service initialized!")

    # Register CLI commands safely
    try:
        from service.common import cli_commands
        if hasattr(cli_commands, "db_create"):
            app.cli.add_command(cli_commands.db_create)
        if hasattr(cli_commands, "db_drop"):
            app.cli.add_command(cli_commands.db_drop)
    except Exception as e:
        app.logger.warning(f"CLI commands not registered: {e}")

    return app


# Flask CLI instance
app = create_app()
