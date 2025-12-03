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
This module creates the Flask app, initializes the database,
registers routes, and sets up logging for the Promotions service.
"""

from flask import Flask
from service import config
from service.common import log_handlers


def create_app():
    """Initialize and configure the Flask application."""
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.from_object(config)

    # Disable strict slashes (required by tests)
    app.url_map.strict_slashes = False

    # Initialize database
    from service.models import db  # noqa: E402
    db.init_app(app)

    with app.app_context():
        # Import routes AFTER app is created
        from service import routes  # noqa: F401,E402
        from service.common import error_handlers  # noqa: F401,E402

        # Create DB tables
        try:
            db.create_all()
        except Exception as error:  # noqa: BLE001
            app.logger.warning("Database not ready: %s", error)

        # Setup logging
        log_handlers.init_logging(app, "gunicorn.error")

        app.logger.info(70 * "*")
        app.logger.info(" PROMOTION SERVICE RUNNING ".center(70, "*"))
        app.logger.info(70 * "*")
        app.logger.info("Service initialized!")

    return app


# Create the Flask application instance
app = create_app()


def _init_logging_and_handlers():
    """Register error handlers explicitly for testing."""
    from service.common import error_handlers  # noqa: E402
    error_handlers.register_handlers(app)
    app.logger.info("Handlers registered.")


_init_logging_and_handlers()
