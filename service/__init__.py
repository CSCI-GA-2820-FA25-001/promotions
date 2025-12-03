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

from flask import Flask
from service import config
from service.common import log_handlers


def create_app():
    """Create and configure the Flask application."""
    # pylint: disable=import-outside-toplevel

    flask_app = Flask(__name__)
    flask_app.config.from_object(config)

    flask_app.url_map.strict_slashes = False

    # ---- Database setup ----
    from service.models import db
    db.init_app(flask_app)

    with flask_app.app_context():
        from service import routes  # pylint: disable=unused-import
        from service.common import error_handlers  # pylint: disable=unused-import

        try:
            db.create_all()
        except Exception as error:  # pylint: disable=broad-exception-caught
            flask_app.logger.warning("%s: Database not ready yet", error)

        log_handlers.init_logging(flask_app, "gunicorn.error")

        flask_app.logger.info(70 * "*")
        flask_app.logger.info("PROMOTION SERVICE RUNNING".center(70, "*"))
        flask_app.logger.info(70 * "*")
        flask_app.logger.info("Service initialized!")

    return flask_app
