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

from flask import jsonify, request, url_for, current_app
from service.models import Promotion, StatusEnum, DataValidationError
from service.common import status  # HTTP Status Codes
from datetime import datetime
import logging


logger = logging.getLogger("flask.app")


######################################################################
# GET INDEX (#10 Root URL)
######################################################################
def index():
    """Root URL for the Promotions microservice"""
    logger.info("Root URL accessed.")
    response = {
        "service": "Promotions REST API Service",
        "version": "1.0",
        "description": "This service manages promotions for an eCommerce platform.",
        # ✅ use host_url instead of _external for test consistency
        "list_url": request.host_url.rstrip("/") + url_for("list_promotions"),
    }
    return jsonify(response), status.HTTP_200_OK


######################################################################
# H E L P E R   F U N C T I O N S
######################################################################


def require_admin():
    """Check if request has administrator privileges"""
    role = request.headers.get("X-Role")

    if not role:
        return (
            jsonify({"error": "Unauthorized", "message": "Authentication required"}),
            status.HTTP_401_UNAUTHORIZED,
        )

    if role != "administrator":
        return (
            jsonify(
                {
                    "error": "Forbidden",
                    "message": "Administrator privileges required to create promotions",
                }
            ),
            status.HTTP_403_FORBIDDEN,
        )

    return None


def validate_business_logic(data):
    """Validate business rules. Returns (error_response, status_code) or (None, None)"""
    # Check original_price > 0
    if data.get("original_price") and float(data["original_price"]) <= 0:
        return (
            jsonify(
                {
                    "error": "Unprocessable Entity",
                    "message": "original_price must be greater than 0",
                }
            ),
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # Check discount logic
    promotion_type = data.get("promotion_type")
    discount_value = data.get("discount_value")
    discount_type = data.get("discount_type")
    original_price = data.get("original_price")

    # If promotion_type is 'other', discount fields must be null
    if promotion_type == "other":
        if discount_value is not None or discount_type is not None:
            return (
                jsonify(
                    {
                        "error": "Unprocessable Entity",
                        "message": "discount_value and discount_type must be null when promotion_type is not 'discount'",
                    }
                ),
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

    # If promotion_type is 'discount', validate discount logic
    if promotion_type == "discount" and discount_value is not None:
        if discount_type == "amount":
            if float(discount_value) > float(original_price):
                return (
                    jsonify(
                        {
                            "error": "Unprocessable Entity",
                            "message": "discount_value cannot exceed original_price for amount-based discounts",
                        }
                    ),
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
        elif discount_type == "percent":
            if float(discount_value) < 0 or float(discount_value) > 100:
                return (
                    jsonify(
                        {
                            "error": "Unprocessable Entity",
                            "message": "discount_value must be between 0 and 100 for percent-based discounts",
                        }
                    ),
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

    # Check dates
    start_date = data.get("start_date")
    expiration_date = data.get("expiration_date")

    if start_date and expiration_date:
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(expiration_date)
            if end <= start:
                return (
                    jsonify(
                        {
                            "error": "Unprocessable Entity",
                            "message": "expiration_date must be after start_date",
                        }
                    ),
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
        except (ValueError, TypeError):
            pass  # Will be caught by deserialize

    return None, None


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


######################################################################
# CREATE PROMOTION
######################################################################
def create_promotion():
    """Create a new Promotion (admin only)"""
    logger.info("Request to create a promotion")

    # Check authentication and authorization
    auth_error = require_admin()
    if auth_error:
        return auth_error

    # Parse JSON
    try:
        data = request.get_json()
    except Exception:
        return (
            jsonify({"error": "Invalid request", "message": "Invalid JSON format"}),
            status.HTTP_400_BAD_REQUEST,
        )

    if not data:
        return (
            jsonify({"error": "Invalid request", "message": "No data provided"}),
            status.HTTP_400_BAD_REQUEST,
        )

    # Validate business logic
    validation_error, validation_status = validate_business_logic(data)
    if validation_error:
        return validation_error, validation_status

    # Check for duplicate product_name
    existing = Promotion.find_by_name(data.get("product_name", ""))
    if existing:
        return (
            jsonify(
                {
                    "error": "Conflict",
                    "message": f"Promotion with name '{data.get('product_name')}' already exists",
                }
            ),
            status.HTTP_409_CONFLICT,
        )

    # Create the promotion
    promotion = Promotion()
    try:
        promotion.deserialize(data)
        promotion.create()

        message = promotion.serialize()
        location_url = url_for("create_promotion", _external=True)

        logger.info("Promotion with ID: %d created.", promotion.id)
        return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}

    except DataValidationError as e:
        logger.error("Data validation error: %s", str(e))
        return (
            jsonify({"error": "Invalid request", "message": str(e)}),
            status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.error("Unexpected error creating promotion: %s", str(e))
        error_msg = str(e).lower()
        if "check constraint" in error_msg or "violates check constraint" in error_msg:
            return (
                jsonify(
                    {
                        "error": "Unprocessable Entity",
                        "message": "Database constraint violation: " + str(e),
                    }
                ),
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return (
            jsonify(
                {
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                }
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

######################################################################
# UPDATE PROMOTION 
######################################################################
@app.route("/promotions/<int:promo_id>", methods=["PUT"])
def update_pets(promo_id):
    """
    Update a Pet

    This endpoint will update a Pet based the body that is posted
    """
    app.logger.info("Request to Update a promo with id [%s]", promo_id)
    check_content_type("application/json")

    # Attempt to find the Pet and abort if not found
    promo = Promotion.find(promo_id)
    if not promo:
        abort(status.HTTP_404_NOT_FOUND, f"Promotion with id '{promo_id}' was not found.")

    # Update the Pet with the new data
    data = request.get_json()
    app.logger.info("Processing: %s", data)
    promo.deserialize(data)

    # Save the updates to the database
    promo.update()

    app.logger.info("Pet with ID: %d updated.", promo.id)
    return jsonify(promo.serialize()), status.HTTP_200_OK
######################################################################
# LIST PROMOTIONS (#8)
######################################################################
def list_promotions():
    """List promotions filtered by role"""
    role = request.args.get("role", "customer")  # default: customer view

    logger.debug(f"Role parameter: {role}")

    if role == "customer":
        # Return only active promotions
        promotions = Promotion.query.filter_by(status=StatusEnum.active).all()
    elif role == "supplier":
        # Return active + expired promotions
        promotions = Promotion.query.filter(
            Promotion.status.in_([StatusEnum.active, StatusEnum.expired])
        ).all()
    elif role == "manager":
        # Return all promotions
        promotions = Promotion.query.all()
    else:
        return jsonify({"message": "Invalid role value"}), status.HTTP_400_BAD_REQUEST

    results = [promo.serialize() for promo in promotions]
    return jsonify(results), status.HTTP_200_OK


######################################################################
# ROUTE REGISTRATION
######################################################################
def init_routes(app):
    """Register all routes with the Flask app"""
    app.add_url_rule("/", "index", index, methods=["GET"])
    app.add_url_rule("/promotions", "list_promotions", list_promotions, methods=["GET"])
    app.add_url_rule(
        "/promotions", "create_promotion", create_promotion, methods=["POST"]
    )


# Auto-register routes when module is imported within app context
try:
    init_routes(current_app._get_current_object())
except RuntimeError:
    # No app context yet, routes will be registered later
    pass
