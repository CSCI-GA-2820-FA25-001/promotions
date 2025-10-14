######################################################################
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
######################################################################

"""
Package: service
This module creates and configures the Flask app and sets up the logging
and SQL database
"""

import sys
from flask import Flask
from service import config
from service.common import log_handlers


######################################################################
# Initialize the Flask instance
######################################################################
def create_app():
    """Initialize the core Flask application."""
    app = Flask(__name__)
    app.config.from_object(config)

    # ------------------------------------------------------------------
    # Initialize database
    # ------------------------------------------------------------------
    from service.models import db
    db.init_app(app)

    # ------------------------------------------------------------------
    # Register blueprints, routes, and CLI commands
    # ------------------------------------------------------------------
    with app.app_context():
        from service import routes, models  # noqa: F401
        from service.common import error_handlers, cli_commands  # noqa: F401

        try:
            db.create_all()
        except Exception as error:  # pylint: disable=broad-except
            app.logger.critical("%s: Cannot continue", error)
            sys.exit(4)

        cli_commands.init_cli(app)

    # ------------------------------------------------------------------
    # Set up logging
    # ------------------------------------------------------------------
    log_handlers.init_logging(app, "gunicorn.error")

    app.logger.info(70 * "*")
    app.logger.info("  S E R V I C E   R U N N I N G  ".center(70, "*"))
    app.logger.info(70 * "*")
    app.logger.info("Service initialized!")

    return app


# ----------------------------------------------------------------------
# Create the Flask app instance
# ----------------------------------------------------------------------
app = create_app()

from service import routes  # noqa: F401

# ----------------------------------------------------------------------
# Trigger logger and handler registration explicitly (for test coverage)
# ----------------------------------------------------------------------
from service.common import error_handlers


def _init_logging_and_handlers():
    """Ensure handlers and logger are initialized at import time."""
    error_handlers.register_handlers(app)
    app.logger.info("Service initialized and handlers registered.")


_init_logging_and_handlers()
