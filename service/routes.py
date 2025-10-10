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
YourResourceModel Service

This service implements a REST API that allows you to Create, Read, Update
and Delete YourResourceModel
"""

from flask import jsonify, request, url_for, abort
from flask import current_app as app  # Import Flask application
from service.models import Promotion, db, StatusEnum, DataValidationError #YourResourceModel
from service.common import status  # HTTP Status Codes
import logging


logger = logging.getLogger("flask.app")


######################################################################
# GET INDEX (#10 Root URL)
######################################################################
@app.route("/", methods=["GET"])
def index():
    """Root URL for the Promotions microservice"""
    logger.info("Root URL accessed.")
    try:
        response = {
            "service": "Promotions Service",
            "version": "1.0.0",
            "description": "Handles creation and management of promotions and discounts.",
            "list_url": url_for("list_promotions", _external=True),
        }
        return jsonify(response), status.HTTP_200_OK
    except Exception as e:
        logger.error(f"Error generating root response: {str(e)}")
        abort(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            description="Internal server error while generating root metadata.",
        )


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################

# Todo: Place your REST API code here ...


######################################################################
# LIST PROMOTIONS (#8)
######################################################################
@app.route("/promotions", methods=["GET"])
def list_promotions():
    """
    List promotions based on user role.

    GET /promotions?role=<customer|supplier|manager>

    Roles:
      - customer → active promotions only
      - supplier → active + expired (excluding deleted)
      - manager  → all promotions

    Returns:
        200 OK with JSON list of promotions
        400 Bad Request for invalid role
        500 Internal Server Error for unexpected failures
    """
    logger.info("Request for promotions list received.")
    role = request.args.get("role", "customer").strip().lower()
    logger.debug(f"Role parameter received: {role}")

    try:
        # ---- Role-based filtering ----
        if role == "customer":
            promotions = Promotion.query.filter_by(status=StatusEnum.active).all()

        elif role == "supplier":
            promotions = Promotion.query.filter(
                Promotion.status.in_([StatusEnum.active, StatusEnum.expired])
            ).all()

        elif role == "manager":
            promotions = Promotion.query.all()

        else:
            logger.warning(f"Invalid role parameter: {role}")
            abort(
                status.HTTP_400_BAD_REQUEST,
                description="Invalid role parameter. Must be one of: customer, supplier, manager.",
            )

        # ---- Serialize and respond ----
        results = [promo.serialize() for promo in promotions]
        logger.info(f"Returning {len(results)} promotions for role '{role}'.")
        return jsonify(results), status.HTTP_200_OK

    except DataValidationError as e:
        logger.error(f"Data validation error while listing promotions: {str(e)}")
        abort(status.HTTP_400_BAD_REQUEST, description=str(e))

    except Exception as e:
        logger.exception(f"Unhandled error in list_promotions: {str(e)}")
        abort(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            description="Internal server error while retrieving promotions.",
        )
