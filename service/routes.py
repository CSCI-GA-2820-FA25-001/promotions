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

import logging
from flask import jsonify, request, url_for
from flask import current_app as app
from service.models import Promotion, StatusEnum, DataValidationError, DiscountTypeEnum, PromotionTypeEnum
from service.common import status
from datetime import datetime


logger = logging.getLogger("flask.app")


######################################################################
# GET INDEX
######################################################################
@app.route("/", methods=["GET"])
def index():
    """Root URL for the Promotions microservice"""
    logger.info("Root URL accessed.")
    response = {
        "service": "Promotions REST API Service",
        "version": "1.0",
        "description": "This service allows CRUD operations on promotions",
        "list_url": url_for("list_promotions", _external=True),
    }
    return jsonify(response), status.HTTP_200_OK

######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


######################################################################
# CREATE
######################################################################


@app.route("/promotions", methods=["POST"])
def create_promotion():
    """Create a new promotion"""
    if not request.is_json:
        return jsonify(error="Unsupported Media Type",
                       message="Content-Type must be application/json"), status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    try:
        data = request.get_json()
        promotion = Promotion()
        promotion.deserialize(data)
        promotion.create()
        location_url = url_for("get_promotion", promotion_id=promotion.id, _external=True)
        return jsonify(promotion.serialize()), status.HTTP_201_CREATED, {"Location": location_url}
    except DataValidationError as err:
        return jsonify(error="Bad Request", message=str(err)), status.HTTP_400_BAD_REQUEST


######################################################################
# READ
######################################################################
@app.route("/promotions/<int:promotion_id>", methods=["GET"])
def get_promotion(promotion_id):
    """Read a promotion"""
    promotion = Promotion.find(promotion_id)
    if not promotion:
        return (
            jsonify(
                error="Not Found",
                message=f"Promotion with id '{promotion_id}' was not found.",
            ),
            status.HTTP_404_NOT_FOUND,
        )
    return jsonify(promotion.serialize()), status.HTTP_200_OK

######################################################################
# UPDATE
######################################################################
@app.route("/promotions/<int:promotion_id>", methods=["PUT"])
def update_promotion(promotion_id):
    """Update a promotion"""
    promotion = Promotion.find(promotion_id)
    if not promotion:
        return jsonify(error="Not Found",
                       message=f"Promotion with id '{promotion_id}' was not found."), status.HTTP_404_NOT_FOUND
    if not request.is_json:
        return jsonify(error="Unsupported Media Type",
                       message="Content-Type must be application/json"), status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    try:
        promotion.deserialize(request.get_json())
        promotion.update()
        return jsonify(promotion.serialize()), status.HTTP_200_OK
    except DataValidationError as err:
        return jsonify(error="Bad Request", message=str(err)), status.HTTP_400_BAD_REQUEST


######################################################################
# DELETE
######################################################################
@app.route("/promotions/<int:promotion_id>", methods=["DELETE"])
def delete_promotion(promotion_id):
    """Delete a promotion"""
    promotion = Promotion.find(promotion_id)
    if not promotion:
        # Idempotent delete — return 204 even if not found
        return "", status.HTTP_204_NO_CONTENT

    # Check for active promotions before deleting
    if promotion.status == StatusEnum.active:
        return (
            jsonify(error="Conflict", message="Cannot delete active promotion"),
            status.HTTP_409_CONFLICT,
        )

    # Proceed with deletion
    promotion.delete()
    return "", status.HTTP_204_NO_CONTENT


######################################################################
# LIST
######################################################################
@app.route("/promotions", methods=["GET"])
def list_promotions():
    """List promotions filtered by role and optionally by date range and keyword"""
    role = (request.headers.get("X-Role") or request.args.get("role", "customer")).lower()
    start_date_str = request.args.get("start_date")
    end_date_str   = request.args.get("end_date")
    keyword        = request.args.get("q") or request.args.get("keyword")

    # 1) Base query by role
    if role == "customer":
        query = Promotion.query.filter(Promotion.status == StatusEnum.active)
    elif role == "supplier":
        query = Promotion.query.filter(Promotion.status.in_([StatusEnum.active, StatusEnum.expired]))
    elif role == "manager":
        query = Promotion.query
    else:
        return jsonify(error="Bad Request", message="Invalid role value"), status.HTTP_400_BAD_REQUEST

    # 2) Keyword search (product_name or description)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            (Promotion.product_name.ilike(like)) | (Promotion.description.ilike(like))
        )

    # 3) Optional date range filter
    try:
        if start_date_str and end_date_str:
            start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
            end_date   = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
            query = query.filter(
                Promotion.start_date >= start_date,
                Promotion.expiration_date <= end_date
            )
    except ValueError:
        return jsonify(error="Bad Request", message="Invalid date format"), status.HTTP_400_BAD_REQUEST

    # 4) Return results
    result = [p.serialize() for p in query.all()]
    return jsonify(result), status.HTTP_200_OK


######################################################################
# DUPLICATE
######################################################################

@app.route("/promotions/<int:promotion_id>/duplicate", methods=["POST"])
def duplicate_promotion(promotion_id):
    """Duplicate an existing promotion"""
    # Check authentication
    role = request.headers.get("X-Role")
    if not role:
        return jsonify(error="Unauthorized", message="Authentication required"), status.HTTP_401_UNAUTHORIZED
    
    # Check authorization (only administrators can duplicate)
    if role.lower() != "administrator":
        return jsonify(error="Forbidden", message="Administrator privileges required to duplicate promotions"), status.HTTP_403_FORBIDDEN
    
    # Check content type
    if not request.is_json:
        return jsonify(error="Unsupported Media Type", message="Content-Type must be application/json"), status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    
    # Find the original promotion
    original_promotion = Promotion.find(promotion_id)
    if not original_promotion:
        return jsonify(error="Not Found", message=f"Promotion with ID {promotion_id} not found"), status.HTTP_404_NOT_FOUND
    
    try:
        # Get override data from request
        override_data = request.get_json() or {}
        
        # Create new promotion data by copying from original and applying overrides
        # Handle product_name - if not overridden, make it unique by appending timestamp
        product_name_override = override_data.get("product_name")
        if product_name_override:
            new_product_name = product_name_override
        else:
            # Make the product name unique by appending timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_product_name = f"{original_promotion.product_name}_copy_{timestamp}"
        
        new_promotion_data = {
            "product_name": new_product_name,
            "description": override_data.get("description", original_promotion.description),
            "original_price": override_data.get("original_price", float(original_promotion.original_price)),
            "discount_value": override_data.get("discount_value", float(original_promotion.discount_value) if original_promotion.discount_value else None),
            "discount_type": override_data.get("discount_type", original_promotion.discount_type.value if original_promotion.discount_type else None),
            "promotion_type": override_data.get("promotion_type", original_promotion.promotion_type.value),
            "expiration_date": override_data.get("expiration_date", original_promotion.expiration_date.isoformat())
        }
        
        # Only add start_date if it exists in original or override
        start_date_override = override_data.get("start_date")
        if start_date_override:
            new_promotion_data["start_date"] = start_date_override
        elif original_promotion.start_date:
            new_promotion_data["start_date"] = original_promotion.start_date.isoformat()
        
        # Create the new promotion using deserialize
        logger.info("Creating promotion with data: %s", new_promotion_data)
        new_promotion = Promotion()
        new_promotion.deserialize(new_promotion_data)
        new_promotion.create()
        
        # Return the created promotion
        location_url = url_for("get_promotion", promotion_id=new_promotion.id, _external=True)
        return jsonify(new_promotion.serialize()), status.HTTP_201_CREATED, {"Location": location_url}
        
    except DataValidationError as err:
        logger.error("DataValidationError in duplicate_promotion: %s", str(err))
        # Check if it's a duplicate name conflict wrapped in DataValidationError
        if "duplicate" in str(err).lower() or "unique" in str(err).lower() or "1062" in str(err):
            return jsonify(error="Conflict", message=f"Promotion name '{override_data.get('product_name', '')}' already exists"), status.HTTP_409_CONFLICT
        return jsonify(error="Unprocessable Entity", message=str(err)), status.HTTP_422_UNPROCESSABLE_ENTITY
    except Exception as err:
        logger.error("Exception in duplicate_promotion: %s", str(err))
        # Handle duplicate name conflicts
        if "duplicate" in str(err).lower() or "unique" in str(err).lower():
            return jsonify(error="Conflict", message=f"Promotion name '{override_data.get('product_name', '')}' already exists"), status.HTTP_409_CONFLICT
        # Handle other validation errors
        return jsonify(error="Bad Request", message=str(err)), status.HTTP_400_BAD_REQUEST


######################################################################
# METHOD NOT ALLOWED
######################################################################


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle method not allowed"""
    return jsonify(error="Method Not Allowed", message=str(error)), status.HTTP_405_METHOD_NOT_ALLOWED
